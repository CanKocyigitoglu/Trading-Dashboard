"""Postgres integration tests for market persistence.

These exercise real database behaviour the rules require to be tested against
PostgreSQL: idempotent ingestion (the ON CONFLICT path), the audit record, and
the DB-backed overview. They are skipped when ``DATABASE_URL`` is unset and they
mock the network boundary (``fetch_frame``) so they never call Yahoo.

Each test runs against a dedicated, throwaway schema (``it_market``) and inside
one transaction that is rolled back on teardown
(``join_transaction_mode="create_savepoint"`` keeps the service's commit inside a
savepoint). The schema isolates the fixed test timestamps from real ingested data
in ``public`` (same ``UNIQUE(symbol, source_ts)``), and nothing is left behind.
"""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal

import pandas as pd
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.adapters import yahoo_market_source as yh
from app.adapters.yahoo_market_source import Observation
from app.config import Settings, get_settings
from app.db import Base, normalise_database_url
from app.repositories import market_repository
from app.services import ingestion, market

WTI = yh.BY_SYMBOL["WTI"]
GOLD = yh.BY_SYMBOL["GOLD"]

TEST_SCHEMA = "it_market"  # isolated from real data in `public`


@pytest.fixture
def db_session():
    settings = get_settings()
    if not settings.database_url:
        pytest.skip("DATABASE_URL not set; skipping Postgres integration tests")
    engine = create_engine(normalise_database_url(settings.database_url))

    # Create the test tables in a fresh throwaway schema; schema_translate_map
    # redirects the (schema-less) models into it for both DDL and queries.
    with engine.connect() as setup:
        setup.exec_driver_sql(f"DROP SCHEMA IF EXISTS {TEST_SCHEMA} CASCADE")
        setup.exec_driver_sql(f"CREATE SCHEMA {TEST_SCHEMA}")
        setup.commit()
    connection = engine.connect().execution_options(schema_translate_map={None: TEST_SCHEMA})
    Base.metadata.create_all(connection, checkfirst=False)
    connection.commit()

    outer = connection.begin()
    session = Session(bind=connection, join_transaction_mode="create_savepoint")
    try:
        yield session
    finally:
        session.close()
        outer.rollback()  # discard everything this test wrote
        connection.close()
        with engine.connect() as teardown:
            teardown.exec_driver_sql(f"DROP SCHEMA IF EXISTS {TEST_SCHEMA} CASCADE")
            teardown.commit()
        engine.dispose()


def _obs(symbol_inst, minute: int, price: str) -> Observation:
    return Observation(
        symbol=symbol_inst.symbol,
        source_symbol=symbol_inst.source_symbol,
        price=Decimal(price),
        currency=symbol_inst.currency,
        unit=symbol_inst.unit,
        source_ts=datetime(2026, 6, 25, 13, minute, tzinfo=UTC),
        data_quality="ok",
    )


def test_insert_is_idempotent(db_session):
    batch = [_obs(WTI, 0, "78.10"), _obs(WTI, 1, "78.25")]
    assert market_repository.insert_observations(db_session, batch) == 2
    # Re-inserting the same (symbol, source_ts) writes nothing.
    assert market_repository.insert_observations(db_session, batch) == 0
    # A new bar for the same symbol inserts one row.
    assert market_repository.insert_observations(db_session, [_obs(WTI, 2, "78.40")]) == 1

    latest = market_repository.latest_per_symbol(db_session, ["WTI"])
    assert len(latest) == 1
    assert latest[0].price == Decimal("78.40")
    assert latest[0].source_ts == datetime(2026, 6, 25, 13, 2, tzinfo=UTC)


def test_history_returns_most_recent_points_oldest_first(db_session):
    # Insert 5 minute-bars; ask for the latest 3.
    market_repository.insert_observations(db_session, [_obs(WTI, m, f"78.{m}0") for m in range(5)])
    rows = market_repository.history(db_session, "WTI", limit=3)

    # The newest 3 (minutes 2,3,4), presented oldest first — not the oldest 3.
    assert [r.source_ts.minute for r in rows] == [2, 3, 4]


def test_run_ingestion_persists_and_audits(db_session, monkeypatch):
    def fake_fetch(source_symbol, period, interval):
        index = pd.to_datetime(["2026-06-25T13:00:00Z", "2026-06-25T13:01:00Z"])
        price = 78.0 if source_symbol == "CL=F" else 2400.0
        return pd.DataFrame({"Close": [price, price + 0.5]}, index=index)

    monkeypatch.setattr(yh, "fetch_frame", fake_fetch)

    clock = iter(
        [datetime(2026, 6, 25, 13, 5, tzinfo=UTC), datetime(2026, 6, 25, 13, 5, 2, tzinfo=UTC)]
    )
    run = ingestion.run_ingestion(db_session, instruments=(WTI, GOLD), clock=lambda: next(clock))

    assert run.status == "success"
    assert run.symbols_requested == 2
    assert run.rows_written == 4  # 2 bars x 2 instruments
    assert run.message is None

    runs = market_repository.recent_runs(db_session, 5)
    assert runs[0].id == run.id


def test_overview_from_db_reads_latest_and_flags_stale(db_session, monkeypatch):
    def fake_fetch(source_symbol, period, interval):
        index = pd.to_datetime(["2026-06-25T13:00:00Z", "2026-06-25T13:01:00Z"])
        return pd.DataFrame({"Close": [78.0, 78.5]}, index=index)

    monkeypatch.setattr(yh, "fetch_frame", fake_fetch)
    ingestion.run_ingestion(
        db_session,
        instruments=(WTI,),
        clock=lambda: datetime(2026, 6, 25, 13, 5, tzinfo=UTC),
    )

    settings = Settings(market_source="yahoo", database_url=get_settings().database_url)
    # Evaluate 20 minutes after the last bar -> beyond the 900s default -> stale.
    overview = market.get_market_overview(
        db_session, now=datetime(2026, 6, 25, 13, 25, tzinfo=UTC), settings=settings
    )

    assert overview.synthetic is False
    assert overview.source == "yahoo"
    wti = next(q for q in overview.quotes if q.symbol == "WTI")
    assert wti.last_price == 78.5
    assert wti.previous_price == 78.0
    assert wti.currency == "USD"
    assert wti.stale is True
