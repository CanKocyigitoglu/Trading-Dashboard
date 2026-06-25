"""Typed API response models (the API contract surface).

Monetary values are computed in ``Decimal`` in the domain layer and converted
to JSON numbers here, at the boundary to the presentation layer, purely for
display. ``None`` is preserved so the frontend can distinguish an unavailable
value from zero.
"""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel


class PositionOut(BaseModel):
    position_id: str
    desk: str
    trader: str
    instrument: str
    commodity: str
    unit: str
    currency: str
    side: str
    quantity: float
    avg_price: float
    market_price: float | None
    market_value: float | None
    unrealised_pl: float | None
    var_1d: float | None
    exposure_limit: float
    utilisation_pct: float | None
    as_of: datetime
    data_quality: str


class PositionsResponse(BaseModel):
    items: list[PositionOut]
    total: int
    limit: int
    offset: int
    currency: str | None
    source_timestamp: datetime | None


class SummaryOut(BaseModel):
    currency: str
    net_exposure: float
    gross_exposure: float
    total_unrealised_pl: float
    total_var_1d_illustrative: float
    position_count: int
    incomplete_position_count: int
    source_timestamp: datetime
    evaluation_timestamp: datetime


class AlertOut(BaseModel):
    rule_id: str
    severity: str
    entity_type: str
    desk: str | None
    trader: str | None
    instrument: str | None
    observed: str
    threshold: str
    reason: str
    detail_reference: str | None
    evaluation_timestamp: datetime
    status: str


class AlertsResponse(BaseModel):
    items: list[AlertOut]
    evaluation_timestamp: datetime


class FilterOptions(BaseModel):
    """Distinct values offered to the frontend filter controls."""

    desks: list[str]
    traders: list[str]
    commodities: list[str]


class MarketSeriesPoint(BaseModel):
    """One point on a price series. ``t`` is the source bar/quote time in UTC."""

    t: datetime
    price: float


class MarketQuote(BaseModel):
    """A market quote for one commodity.

    ``change`` is the move versus the previous point and ``change_pct`` is that
    move as a percentage; ``change_pct`` is ``None`` when the previous price is
    zero so an unavailable ratio is never shown as zero. ``source_ts`` is the
    latest source timestamp and ``ingested_at`` when it was persisted; ``stale``
    is set when ``source_ts`` is older than the configured staleness threshold.
    """

    symbol: str
    name: str
    commodity: str
    unit: str
    currency: str
    last_price: float
    previous_price: float
    change: float
    change_pct: float | None
    as_of: datetime
    source_ts: datetime | None
    ingested_at: datetime | None
    stale: bool
    series: list[MarketSeriesPoint]


class MarketOverviewResponse(BaseModel):
    """Latest market snapshot. ``synthetic`` is ``True`` only in offline mode."""

    as_of: datetime
    source: str
    synthetic: bool
    stale_after_seconds: int
    quotes: list[MarketQuote]


class MarketHistoryResponse(BaseModel):
    """Persisted price history for one commodity, oldest point first."""

    symbol: str
    name: str
    commodity: str
    unit: str
    currency: str
    source: str
    count: int
    points: list[MarketSeriesPoint]


class IngestionRunOut(BaseModel):
    """One ingestion audit record (the control/management surface)."""

    id: int
    source: str
    started_at: datetime
    finished_at: datetime | None
    status: str
    symbols_requested: int
    rows_written: int
    message: str | None


class IngestionRunsResponse(BaseModel):
    items: list[IngestionRunOut]
