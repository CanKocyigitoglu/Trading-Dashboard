"""Position valuation: framework-independent financial calculations.

These functions contain the approved business definitions for the first
trading-risk slice. They are pure (no I/O, no framework types) and use
``Decimal`` so monetary arithmetic is exact; rounding happens only at the
presentation boundary.

Sign convention
---------------
``quantity`` is signed: a long position is positive, a short position is
negative. Therefore::

    market_value  = quantity * market_price            (signed)
    unrealised_pl = quantity * (market_price - avg_price)

A short position gains when the market price falls.

Missing data
------------
``market_price`` and ``var_1d`` may be unavailable. Unavailable is represented
as ``None`` and is kept strictly distinct from zero: a missing input
propagates to ``None`` in any value derived from it -- it is never treated as
zero.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from enum import StrEnum


class Side(StrEnum):
    LONG = "Long"
    SHORT = "Short"
    FLAT = "Flat"


class DataQuality(StrEnum):
    COMPLETE = "complete"
    INCOMPLETE = "incomplete"  # at least one required value is missing


# Inputs required for a position to be fully valued.
REQUIRED_INPUTS = ("market_price", "var_1d")


@dataclass(frozen=True)
class Position:
    """A single source position record, with source precision preserved."""

    position_id: str
    desk: str
    trader: str
    instrument: str
    commodity: str
    unit: str
    currency: str
    quantity: Decimal  # signed: long > 0, short < 0
    avg_price: Decimal
    market_price: Decimal | None  # None == unavailable, distinct from zero
    var_1d: Decimal | None  # supplied 1-day VaR; None == unavailable
    exposure_limit: Decimal
    as_of: datetime  # source timestamp, timezone-aware UTC


@dataclass(frozen=True)
class ValuedPosition:
    """A position plus its derived values. ``None`` means not computable."""

    position: Position
    side: Side
    market_value: Decimal | None
    unrealised_pl: Decimal | None
    utilisation_pct: Decimal | None
    data_quality: DataQuality


def compute_side(quantity: Decimal) -> Side:
    if quantity > 0:
        return Side.LONG
    if quantity < 0:
        return Side.SHORT
    return Side.FLAT


def compute_market_value(quantity: Decimal, market_price: Decimal | None) -> Decimal | None:
    if market_price is None:
        return None
    return quantity * market_price


def compute_unrealised_pl(
    quantity: Decimal, avg_price: Decimal, market_price: Decimal | None
) -> Decimal | None:
    if market_price is None:
        return None
    return quantity * (market_price - avg_price)


def compute_utilisation_pct(
    market_value: Decimal | None, exposure_limit: Decimal
) -> Decimal | None:
    """Gross exposure as a percentage of the position's exposure limit."""
    if market_value is None or exposure_limit == 0:
        return None
    return abs(market_value) / exposure_limit * Decimal(100)


def data_quality(position: Position) -> DataQuality:
    if position.market_price is None or position.var_1d is None:
        return DataQuality.INCOMPLETE
    return DataQuality.COMPLETE


def value_position(position: Position) -> ValuedPosition:
    """Compute all derived values for a position in one place."""
    market_value = compute_market_value(position.quantity, position.market_price)
    return ValuedPosition(
        position=position,
        side=compute_side(position.quantity),
        market_value=market_value,
        unrealised_pl=compute_unrealised_pl(
            position.quantity, position.avg_price, position.market_price
        ),
        utilisation_pct=compute_utilisation_pct(market_value, position.exposure_limit),
        data_quality=data_quality(position),
    )
