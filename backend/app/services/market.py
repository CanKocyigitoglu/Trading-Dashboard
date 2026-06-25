"""Use-case orchestration for the Live Market page.

In ``yahoo`` mode the snapshot is read from the persisted history (populated by
the ingestion process); in ``synthetic`` mode it comes from the offline
generator. ``now`` is injectable so staleness and timestamps are reproducible in
tests, mirroring ``dashboard.get_summary``.
"""

from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy.orm import Session

from ..adapters import market_data_source
from ..adapters import yahoo_market_source as yh
from ..config import Settings, get_settings
from ..db_models import IngestionRun, MarketObservation
from ..repositories import market_repository
from ..schemas.models import (
    IngestionRunOut,
    IngestionRunsResponse,
    MarketHistoryResponse,
    MarketOverviewResponse,
    MarketQuote,
    MarketSeriesPoint,
)

# Points shown in the per-commodity overview spark series (deeper ranges use
# the dedicated /market/history endpoint).
OVERVIEW_SERIES_POINTS = 60

_UNIVERSE_ORDER = {sym: i for i, sym in enumerate(yh.BY_SYMBOL)}


def get_market_overview(
    session: Session | None, now: datetime | None = None, settings: Settings | None = None
) -> MarketOverviewResponse:
    settings = settings or get_settings()
    now = now or datetime.now(UTC)
    if settings.market_source == "synthetic":
        return market_data_source.build_overview(now, settings.market_stale_after_seconds)
    assert session is not None  # the route's dependency guarantees a DB session here
    return _overview_from_db(session, now, settings.market_stale_after_seconds)


def _overview_from_db(
    session: Session, now: datetime, stale_after_seconds: int
) -> MarketOverviewResponse:
    quotes = [
        _quote_from_db(session, latest, now, stale_after_seconds)
        for latest in market_repository.latest_per_symbol(session)
    ]
    quotes.sort(key=lambda q: _UNIVERSE_ORDER.get(q.symbol, len(_UNIVERSE_ORDER)))
    as_of = max((q.source_ts for q in quotes if q.source_ts), default=now)
    return MarketOverviewResponse(
        as_of=as_of,
        source="yahoo",
        synthetic=False,
        stale_after_seconds=stale_after_seconds,
        quotes=quotes,
    )


def _quote_from_db(
    session: Session, latest: MarketObservation, now: datetime, stale_after_seconds: int
) -> MarketQuote:
    inst = yh.BY_SYMBOL.get(latest.symbol)
    rows = market_repository.recent_series(session, latest.symbol, OVERVIEW_SERIES_POINTS)
    points = [MarketSeriesPoint(t=r.source_ts, price=float(r.price)) for r in rows]

    last = float(latest.price)
    previous = float(rows[-2].price) if len(rows) >= 2 else last
    change = round(last - previous, 6)
    change_pct = None if previous == 0 else round(change / previous * 100, 6)
    stale = (now - latest.source_ts).total_seconds() > stale_after_seconds

    return MarketQuote(
        symbol=latest.symbol,
        name=inst.name if inst else latest.symbol,
        commodity=inst.commodity if inst else latest.symbol,
        unit=latest.unit,
        currency=latest.currency,
        last_price=last,
        previous_price=previous,
        change=change,
        change_pct=change_pct,
        as_of=latest.source_ts,
        source_ts=latest.source_ts,
        ingested_at=latest.ingested_at,
        stale=stale,
        series=points,
    )


def _as_utc(dt: datetime | None) -> datetime | None:
    """Treat a tz-naive query bound as UTC so it can be compared to source_ts."""
    if dt is None:
        return None
    return dt if dt.tzinfo is not None else dt.replace(tzinfo=UTC)


def get_market_history(
    session: Session,
    symbol: str,
    *,
    since: datetime | None = None,
    until: datetime | None = None,
    limit: int = 5000,
) -> MarketHistoryResponse:
    rows = market_repository.history(
        session, symbol, since=_as_utc(since), until=_as_utc(until), limit=limit
    )
    inst = yh.BY_SYMBOL.get(symbol)
    # Prefer the stored unit/currency (what the values actually mean); fall back
    # to the instrument definition when the symbol has no rows yet.
    unit = rows[-1].unit if rows else (inst.unit if inst else "")
    currency = rows[-1].currency if rows else (inst.currency if inst else "")
    return MarketHistoryResponse(
        symbol=symbol,
        name=inst.name if inst else symbol,
        commodity=inst.commodity if inst else symbol,
        unit=unit,
        currency=currency,
        source="yahoo",
        count=len(rows),
        points=[MarketSeriesPoint(t=r.source_ts, price=float(r.price)) for r in rows],
    )


def run_to_out(run: IngestionRun) -> IngestionRunOut:
    return IngestionRunOut(
        id=run.id,
        source=run.source,
        started_at=run.started_at,
        finished_at=run.finished_at,
        status=run.status,
        symbols_requested=run.symbols_requested,
        rows_written=run.rows_written,
        message=run.message,
    )


def list_ingestion_runs(session: Session, limit: int = 20) -> IngestionRunsResponse:
    return IngestionRunsResponse(
        items=[run_to_out(r) for r in market_repository.recent_runs(session, limit)]
    )
