"""Alembic environment: pulls the database URL from app settings.

The URL lives in ``backend/.env`` (git-ignored) via :mod:`app.config`, so it is
never duplicated in ``alembic.ini``. Importing :mod:`app.db_models` registers
every table on ``Base.metadata`` for autogenerate and migrations.
"""

from __future__ import annotations

from logging.config import fileConfig

from sqlalchemy import engine_from_config, pool

import app.db_models  # noqa: F401  (registers tables on Base.metadata)
from alembic import context
from app.config import get_settings
from app.db import Base, normalise_database_url

config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

settings = get_settings()
if settings.database_url:
    config.set_main_option("sqlalchemy.url", normalise_database_url(settings.database_url))

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")
    if not url:
        raise RuntimeError("DATABASE_URL is not set; cannot run migrations offline.")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    section = config.get_section(config.config_ini_section, {})
    if not section.get("sqlalchemy.url"):
        raise RuntimeError("DATABASE_URL is not set; configure backend/.env to run migrations.")
    connectable = engine_from_config(section, prefix="sqlalchemy.", poolclass=pool.NullPool)
    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
