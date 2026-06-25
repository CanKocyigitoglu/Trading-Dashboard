"""Application queries for persisted market data.

Repositories own database access; routes never see ORM objects directly. Inserts
are idempotent: ``ON CONFLICT (symbol, source_ts) DO NOTHING`` means re-ingesting
the same bar writes nothing, and the count returned is the number of genuinely
new rows. Callers own the transaction boundary (commit/rollback).
"""

from __future__ import annotations

from collections.abc import Iterable, Sequence
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.orm import Session

from ..adapters.yahoo_market_source import Observation
from ..db_models import IngestionRun, MarketObservation


def insert_observations(session: Session, observations: Iterable[Observation]) -> int:
    """Idempotently insert observations; return the count of newly written rows."""
    rows = [
        {
            "symbol": o.symbol,
            "source_symbol": o.source_symbol,
            "price": o.price,
            "currency": o.currency,
            "unit": o.unit,
            "source_ts": o.source_ts,
            "data_quality": o.data_quality,
        }
        for o in observations
    ]
    if not rows:
        return 0
    stmt = (
        pg_insert(MarketObservation)
        .values(rows)
        .on_conflict_do_nothing(constraint="uq_market_obs_symbol_source_ts")
        .returning(MarketObservation.id)
    )
    return len(session.execute(stmt).fetchall())


def latest_per_symbol(
    session: Session, symbols: Sequence[str] | None = None
) -> list[MarketObservation]:
    """The most recent observation for each symbol (DISTINCT ON source_ts desc)."""
    stmt = (
        select(MarketObservation)
        .order_by(MarketObservation.symbol, MarketObservation.source_ts.desc())
        .distinct(MarketObservation.symbol)
    )
    if symbols:
        stmt = stmt.where(MarketObservation.symbol.in_(symbols))
    return list(session.scalars(stmt))


def recent_series(session: Session, symbol: str, limit: int) -> list[MarketObservation]:
    """The latest ``limit`` observations for ``symbol``, returned oldest first."""
    stmt = (
        select(MarketObservation)
        .where(MarketObservation.symbol == symbol)
        .order_by(MarketObservation.source_ts.desc())
        .limit(limit)
    )
    rows = list(session.scalars(stmt))
    rows.reverse()
    return rows


def history(
    session: Session,
    symbol: str,
    *,
    since: datetime | None = None,
    until: datetime | None = None,
    limit: int = 5000,
) -> list[MarketObservation]:
    """The most recent ``limit`` observations for ``symbol`` over an optional
    range, returned oldest first.

    The limit is applied to the newest rows (``ORDER BY source_ts DESC``) so a
    chart shows the current tail of the series, not the oldest stored points.
    """
    stmt = select(MarketObservation).where(MarketObservation.symbol == symbol)
    if since is not None:
        stmt = stmt.where(MarketObservation.source_ts >= since)
    if until is not None:
        stmt = stmt.where(MarketObservation.source_ts <= until)
    stmt = stmt.order_by(MarketObservation.source_ts.desc()).limit(limit)
    rows = list(session.scalars(stmt))
    rows.reverse()  # newest `limit` rows, presented oldest first
    return rows


def record_ingestion_run(
    session: Session,
    *,
    source: str,
    started_at: datetime,
    finished_at: datetime,
    status: str,
    symbols_requested: int,
    rows_written: int,
    message: str | None,
) -> IngestionRun:
    """Insert one ingestion audit record and flush it to assign an id."""
    run = IngestionRun(
        source=source,
        started_at=started_at,
        finished_at=finished_at,
        status=status,
        symbols_requested=symbols_requested,
        rows_written=rows_written,
        message=message,
    )
    session.add(run)
    session.flush()
    return run


def recent_runs(session: Session, limit: int = 20) -> list[IngestionRun]:
    """The most recent ingestion runs, newest first."""
    stmt = (
        select(IngestionRun)
        .order_by(IngestionRun.started_at.desc(), IngestionRun.id.desc())
        .limit(limit)
    )
    return list(session.scalars(stmt))
