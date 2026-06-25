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
