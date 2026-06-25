"""ORM models for persisted market data (the application-owned history).

These store an *application-owned, clearly-labelled curated snapshot* of a free,
unofficial market source — not a copy of the firm's authoritative pricing estate.
Source time and ingestion time are kept separate; currency and unit are explicit
columns so a stored price is interpretable on its own. ``price`` is ``Numeric``
(maps to PostgreSQL ``numeric``) so source precision is preserved.
"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from sqlalchemy import BigInteger, DateTime, Integer, Numeric, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from .db import Base


class MarketObservation(Base):
    """One price observation for one instrument at one source timestamp.

    ``UNIQUE(symbol, source_ts)`` makes re-ingesting the same bar idempotent.
    """

    __tablename__ = "market_observation"
    __table_args__ = (
        UniqueConstraint("symbol", "source_ts", name="uq_market_obs_symbol_source_ts"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    symbol: Mapped[str] = mapped_column(String(32), index=True)  # canonical, e.g. "WTI"
    source_symbol: Mapped[str] = mapped_column(String(32))  # source id, e.g. "CL=F"
    price: Mapped[Decimal] = mapped_column(Numeric)  # source precision preserved
    currency: Mapped[str] = mapped_column(String(8))
    unit: Mapped[str] = mapped_column(String(16))
    source_ts: Mapped[datetime] = mapped_column(DateTime(timezone=True))  # quote/bar time
    ingested_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    data_quality: Mapped[str] = mapped_column(String(16))  # "ok" | "stale"


class IngestionRun(Base):
    """Audit record for one ingestion cycle (the control/management surface)."""

    __tablename__ = "ingestion_run"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    source: Mapped[str] = mapped_column(String(32))  # e.g. "yahoo"
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    status: Mapped[str] = mapped_column(String(16))  # "success" | "partial" | "failed"
    symbols_requested: Mapped[int] = mapped_column(Integer)
    rows_written: Mapped[int] = mapped_column(Integer)  # newly inserted (duplicates excluded)
    message: Mapped[str | None] = mapped_column(Text, nullable=True)
