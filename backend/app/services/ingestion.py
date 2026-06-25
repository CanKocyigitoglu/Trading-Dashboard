"""Ingestion use case: fetch market data, persist it idempotently, audit the run.

Per-instrument upstream failures are isolated so one bad ticker cannot abort the
cycle; the run's status records whether all, some or no instruments succeeded.
The observation write and its audit record commit together in one transaction.
"""

from __future__ import annotations

from collections.abc import Callable, Sequence
from datetime import UTC, datetime

from sqlalchemy.orm import Session

from ..adapters import yahoo_market_source as yh
from ..adapters.yahoo_market_source import Instrument, Observation
from ..db_models import IngestionRun
from ..repositories import market_repository

SOURCE = "yahoo"


def _status_for(succeeded: int, failed: int) -> str:
    """All ok -> success; none ok -> failed; mixed -> partial."""
    if failed == 0:
        return "success"
    if succeeded == 0:
        return "failed"
    return "partial"


def run_ingestion(
    session: Session,
    *,
    instruments: Sequence[Instrument] = yh.INSTRUMENT_UNIVERSE,
    period: str = yh.DEFAULT_PERIOD,
    interval: str = yh.DEFAULT_INTERVAL,
    clock: Callable[[], datetime] = lambda: datetime.now(UTC),
) -> IngestionRun:
    started_at = clock()
    observations: list[Observation] = []
    errors: list[str] = []
    succeeded = 0
    for inst in instruments:
        try:
            frame = yh.fetch_frame(inst.source_symbol, period, interval)
            observations.extend(yh.normalise_frame(inst, frame))
            succeeded += 1
        except Exception as exc:  # noqa: BLE001 — isolate one ticker's upstream failure
            errors.append(f"{inst.symbol} ({inst.source_symbol}): {exc}")

    rows_written = market_repository.insert_observations(session, observations)
    run = market_repository.record_ingestion_run(
        session,
        source=SOURCE,
        started_at=started_at,
        finished_at=clock(),
        status=_status_for(succeeded, len(errors)),
        symbols_requested=len(instruments),
        rows_written=rows_written,
        message="; ".join(errors) or None,
    )
    session.commit()
    return run
