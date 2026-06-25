"""CLI entry point for market-data ingestion (one dedicated scheduler process).

Run one cycle:     python -m app.ingest
Run continuously:  python -m app.ingest --loop --interval 60

Use the OS scheduler (e.g. Windows Task Scheduler) or a single ``--loop`` process
to refresh on a cadence — never a per-FastAPI-worker job, per the backend rules.
"""

from __future__ import annotations

import argparse
import time

from .config import get_settings
from .db import DatabaseNotConfiguredError, get_sessionmaker
from .services import ingestion


def _run_once() -> None:
    session = get_sessionmaker()()
    try:
        run = ingestion.run_ingestion(session)
    finally:
        session.close()
    line = (
        f"[{run.finished_at:%Y-%m-%d %H:%M:%S%z}] status={run.status} "
        f"symbols={run.symbols_requested} rows_written={run.rows_written}"
    )
    print(line + (f" message={run.message}" if run.message else ""))


def main() -> int:
    parser = argparse.ArgumentParser(description="Ingest market data into the database.")
    parser.add_argument("--loop", action="store_true", help="Run continuously.")
    parser.add_argument(
        "--interval", type=int, default=60, help="Seconds between cycles in --loop mode."
    )
    args = parser.parse_args()

    if get_settings().market_source != "yahoo":
        print("MARKET_SOURCE is not 'yahoo'; nothing to ingest.")
        return 0

    try:
        if args.loop:
            print(f"Ingesting every {args.interval}s. Press Ctrl-C to stop.")
            while True:
                _run_once()
                time.sleep(args.interval)
        else:
            _run_once()
    except DatabaseNotConfiguredError as exc:
        print(f"error: {exc}")
        return 1
    except KeyboardInterrupt:
        print("\nstopped.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
