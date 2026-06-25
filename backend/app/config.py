"""Application settings loaded from the environment.

Covers the read-only positions slice (sample CSV, timezone, CORS) and the live
market slice (a database for persisted observations and the market data source).
``database_url`` is optional so the positions dashboard still runs with no DB;
the live-market endpoints raise a clear error when it is unset.
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

_REPO_ROOT = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_timezone: str = "Europe/London"
    cors_origins: list[str] = ["http://localhost:5173"]
    data_source_mode: str = "sample"
    sample_data_path: Path = _REPO_ROOT / "data" / "sample" / "positions.csv"

    # Live market slice. "yahoo" pulls real prices via yfinance; "synthetic" keeps
    # the offline illustrative generator (no DB, no network) for demos and tests.
    market_source: str = "yahoo"
    # A quote is flagged stale when its source timestamp is older than this.
    market_stale_after_seconds: int = 900
    # SQLAlchemy URL for the persisted market history, e.g.
    # postgresql+psycopg://user:pass@host/db?sslmode=require . None disables persistence.
    database_url: str | None = None


@lru_cache
def get_settings() -> Settings:
    return Settings()
