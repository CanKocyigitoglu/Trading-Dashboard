"""HTTP routes for the trading-risk API (version 1).

Routes validate input, delegate to the service layer and return declared
response models. No financial calculation or data access happens here.
"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Query

from ..config import Settings, get_settings
from ..schemas.models import (
    AlertsResponse,
    FilterOptions,
    PositionsResponse,
    SummaryOut,
)
from ..services import dashboard
from ..services.dashboard import Filters

router = APIRouter(prefix="/api/v1")

DeskParam = Annotated[list[str] | None, Query(description="Filter by one or more desks")]
TraderParam = Annotated[list[str] | None, Query(description="Filter by one or more traders")]
CommodityParam = Annotated[list[str] | None, Query(description="Filter by one or more commodities")]


def _filters(
    desk: DeskParam = None,
    trader: TraderParam = None,
    commodity: CommodityParam = None,
) -> Filters:
    return Filters(desks=desk, traders=trader, commodities=commodity)


FiltersDep = Annotated[Filters, Depends(_filters)]
SettingsDep = Annotated[Settings, Depends(get_settings)]


@router.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/filters", response_model=FilterOptions)
def filter_options(settings: SettingsDep) -> FilterOptions:
    return dashboard.get_filter_options(settings.sample_data_path)


@router.get("/positions", response_model=PositionsResponse)
def positions(
    filters: FiltersDep,
    settings: SettingsDep,
    limit: Annotated[int, Query(ge=1, le=500)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> PositionsResponse:
    return dashboard.get_positions(settings.sample_data_path, filters, limit, offset)


@router.get("/summary", response_model=SummaryOut)
def summary(filters: FiltersDep, settings: SettingsDep) -> SummaryOut:
    return dashboard.get_summary(settings.sample_data_path, filters)


@router.get("/alerts", response_model=AlertsResponse)
def alerts(filters: FiltersDep, settings: SettingsDep) -> AlertsResponse:
    return dashboard.get_alerts(settings.sample_data_path, filters)
