"""Create market_observation and ingestion_run tables.

Revision ID: 0001_market_history
Revises:
Create Date: 2026-06-25
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0001_market_history"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "market_observation",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("symbol", sa.String(length=32), nullable=False),
        sa.Column("source_symbol", sa.String(length=32), nullable=False),
        sa.Column("price", sa.Numeric(), nullable=False),
        sa.Column("currency", sa.String(length=8), nullable=False),
        sa.Column("unit", sa.String(length=16), nullable=False),
        sa.Column("source_ts", sa.DateTime(timezone=True), nullable=False),
        sa.Column(
            "ingested_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column("data_quality", sa.String(length=16), nullable=False),
        sa.UniqueConstraint("symbol", "source_ts", name="uq_market_obs_symbol_source_ts"),
    )
    op.create_index("ix_market_observation_symbol", "market_observation", ["symbol"])

    op.create_table(
        "ingestion_run",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("source", sa.String(length=32), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("status", sa.String(length=16), nullable=False),
        sa.Column("symbols_requested", sa.Integer(), nullable=False),
        sa.Column("rows_written", sa.Integer(), nullable=False),
        sa.Column("message", sa.Text(), nullable=True),
    )


def downgrade() -> None:
    op.drop_table("ingestion_run")
    op.drop_index("ix_market_observation_symbol", table_name="market_observation")
    op.drop_table("market_observation")
