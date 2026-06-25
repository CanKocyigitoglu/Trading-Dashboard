"""Application settings loaded from the environment.

Only what the current read-only slice needs: where the sample data lives, the
display timezone, and CORS origins for the dev frontend. Database settings are
intentionally absent until a persistence feature requires them.
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


@lru_cache
def get_settings() -> Settings:
    return Settings()
