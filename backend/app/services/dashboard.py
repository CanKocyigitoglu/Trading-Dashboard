"""Use-case orchestration for the trading-risk dashboard.

Loads positions from the read-only source, applies optional filters, runs the
domain valuations, portfolio summary and alert evaluation, and maps the results
into typed API models. Business definitions stay in the domain and alert
layers; this module only coordinates them.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path

from ..adapters import positions_source
from ..alerts import rules
from ..domain import portfolio
from ..domain.positions import Position, ValuedPosition, value_position
from ..schemas.models import (
    AlertOut,
    AlertsResponse,
    FilterOptions,
    PositionOut,
    PositionsResponse,
    SummaryOut,
)


class EmptySelectionError(Exception):
    """Raised when a filter selection matches no positions."""


@dataclass(frozen=True)
class Filters:
    desks: list[str] | None = None
    traders: list[str] | None = None
    commodities: list[str] | None = None

    def apply(self, positions: list[Position]) -> list[Position]:
        def keep(p: Position) -> bool:
            return (
                (self.desks is None or p.desk in self.desks)
                and (self.traders is None or p.trader in self.traders)
                and (self.commodities is None or p.commodity in self.commodities)
            )

        return [p for p in positions if keep(p)]


def _to_float(value: Decimal | None) -> float | None:
    return None if value is None else float(value)


def _load_valued(path: Path, filters: Filters) -> list[ValuedPosition]:
    positions = filters.apply(positions_source.load_positions(path))
    return [value_position(p) for p in positions]


def _source_timestamp(valued: list[ValuedPosition]) -> datetime | None:
    if not valued:
        return None
    return max(vp.position.as_of for vp in valued)


def _position_out(vp: ValuedPosition) -> PositionOut:
    p = vp.position
    return PositionOut(
        position_id=p.position_id,
        desk=p.desk,
        trader=p.trader,
        instrument=p.instrument,
        commodity=p.commodity,
        unit=p.unit,
        currency=p.currency,
        side=vp.side.value,
        quantity=float(p.quantity),
        avg_price=float(p.avg_price),
        market_price=_to_float(p.market_price),
        market_value=_to_float(vp.market_value),
        unrealised_pl=_to_float(vp.unrealised_pl),
        var_1d=_to_float(p.var_1d),
        exposure_limit=float(p.exposure_limit),
        utilisation_pct=_to_float(vp.utilisation_pct),
        as_of=p.as_of,
        data_quality=vp.data_quality.value,
    )


def get_positions(path: Path, filters: Filters, limit: int, offset: int) -> PositionsResponse:
    valued = _load_valued(path, filters)
    currencies = {vp.position.currency for vp in valued}
    page = valued[offset : offset + limit]
    return PositionsResponse(
        items=[_position_out(vp) for vp in page],
        total=len(valued),
        limit=limit,
        offset=offset,
        currency=currencies.pop() if len(currencies) == 1 else None,
        source_timestamp=_source_timestamp(valued),
    )


def get_summary(path: Path, filters: Filters, now: datetime | None = None) -> SummaryOut:
    now = now or datetime.now(UTC)
    valued = _load_valued(path, filters)
    if not valued:
        raise EmptySelectionError("No positions match the selected filters.")
    summary = portfolio.summarise(valued)
    source_ts = _source_timestamp(valued)
    assert source_ts is not None  # summarise() rejects an empty set
    return SummaryOut(
        currency=summary.currency,
        net_exposure=float(summary.net_exposure),
        gross_exposure=float(summary.gross_exposure),
        total_unrealised_pl=float(summary.total_unrealised_pl),
        total_var_1d_illustrative=float(summary.total_var_1d_illustrative),
        position_count=summary.position_count,
        incomplete_position_count=summary.incomplete_position_count,
        source_timestamp=source_ts,
        evaluation_timestamp=now,
    )


def get_alerts(path: Path, filters: Filters, now: datetime | None = None) -> AlertsResponse:
    now = now or datetime.now(UTC)
    valued = _load_valued(path, filters)
    alerts = rules.evaluate(valued, now=now)
    return AlertsResponse(
        items=[
            AlertOut(
                rule_id=a.rule_id,
                severity=a.severity.value,
                entity_type=a.entity_type,
                desk=a.desk,
                trader=a.trader,
                instrument=a.instrument,
                observed=a.observed,
                threshold=a.threshold,
                reason=a.reason,
                detail_reference=a.detail_reference,
                evaluation_timestamp=a.evaluation_timestamp,
                status=a.status,
            )
            for a in alerts
        ],
        evaluation_timestamp=now,
    )


def get_filter_options(path: Path) -> FilterOptions:
    positions = positions_source.load_positions(path)
    return FilterOptions(
        desks=sorted({p.desk for p in positions}),
        traders=sorted({p.trader for p in positions}),
        commodities=sorted({p.commodity for p in positions}),
    )
