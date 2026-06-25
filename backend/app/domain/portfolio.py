"""Portfolio-level aggregation of valued positions.

Aggregation never crosses currencies without an approved FX rate, so this
module refuses to combine positions denominated in different currencies. The
first slice carries a single reporting currency; cross-currency support is a
future feature that requires a timestamped FX rate and an explicit target
currency.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from .positions import DataQuality, ValuedPosition


class CurrencyAggregationError(ValueError):
    """Raised when positions in different currencies are aggregated."""


@dataclass(frozen=True)
class PortfolioSummary:
    currency: str
    net_exposure: Decimal
    gross_exposure: Decimal
    total_unrealised_pl: Decimal
    # Simple sum of supplied per-position 1-day VaR. Illustrative only: it
    # ignores diversification and is not an authoritative portfolio VaR.
    total_var_1d_illustrative: Decimal
    position_count: int
    incomplete_position_count: int


def _single_currency(valued: list[ValuedPosition]) -> str:
    currencies = {vp.position.currency for vp in valued}
    if len(currencies) > 1:
        raise CurrencyAggregationError(
            f"Cannot aggregate across currencies without an approved FX rate: {sorted(currencies)}"
        )
    return currencies.pop()


def _sum(values: list[Decimal | None]) -> Decimal:
    """Sum, skipping missing values. Missing is excluded, never read as zero."""
    return sum((v for v in values if v is not None), Decimal(0))


def summarise(valued: list[ValuedPosition]) -> PortfolioSummary:
    if not valued:
        raise ValueError("Cannot summarise an empty set of positions.")

    currency = _single_currency(valued)
    market_values = [vp.market_value for vp in valued]

    return PortfolioSummary(
        currency=currency,
        net_exposure=_sum(market_values),
        gross_exposure=_sum([abs(mv) for mv in market_values if mv is not None]),
        total_unrealised_pl=_sum([vp.unrealised_pl for vp in valued]),
        total_var_1d_illustrative=_sum([vp.position.var_1d for vp in valued]),
        position_count=len(valued),
        incomplete_position_count=sum(
            1 for vp in valued if vp.data_quality is DataQuality.INCOMPLETE
        ),
    )
