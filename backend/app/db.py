"""Database engine, session factory and the FastAPI session dependency.

One engine per process; one session per request or unit of work (project rule).
``database_url`` is optional in settings, so the engine is created lazily and a
clear error is raised when a persistence feature is used without a configured DB.
"""

from __future__ import annotations

from collections.abc import Iterator
from functools import lru_cache

from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from .config import get_settings


class Base(DeclarativeBase):
    """Declarative base shared by all ORM models and Alembic's metadata."""


class DatabaseNotConfiguredError(RuntimeError):
    """Raised when a persistence feature is used but ``DATABASE_URL`` is unset."""


def normalise_database_url(url: str) -> str:
    """Ensure the URL names the psycopg driver SQLAlchemy needs.

    Neon and most tools emit ``postgresql://``; SQLAlchemy 2.x needs an explicit
    driver, so we map it to ``postgresql+psycopg://``. Other schemes pass through.
    """
    prefix = "postgresql://"
    if url.startswith(prefix):
        return "postgresql+psycopg://" + url[len(prefix) :]
    return url


@lru_cache
def get_engine() -> Engine:
    settings = get_settings()
    if not settings.database_url:
        raise DatabaseNotConfiguredError(
            "DATABASE_URL is not set; configure a Postgres URL in backend/.env to "
            "enable market history persistence."
        )
    # pool_pre_ping recovers from connections dropped by Neon's autosuspend.
    return create_engine(normalise_database_url(settings.database_url), pool_pre_ping=True)


@lru_cache
def get_sessionmaker() -> sessionmaker[Session]:
    return sessionmaker(bind=get_engine(), expire_on_commit=False)


def get_session() -> Iterator[Session]:
    """FastAPI dependency: one session per request, always closed."""
    session = get_sessionmaker()()
    try:
        yield session
    finally:
        session.close()
