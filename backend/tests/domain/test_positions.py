"""Tests for position valuation (domain calculations)."""

from __future__ import annotations

from decimal import Decimal

from app.domain.positions import DataQuality, Side, value_position


def test_long_position_values(make_position):
    vp = value_position(
        make_position(quantity=Decimal("100"), avg_price=Decimal("10"), market_price=Decimal("12"))
    )
    assert vp.side is Side.LONG
    assert vp.market_value == Decimal("1200")
    assert vp.unrealised_pl == Decimal("200")
    assert vp.data_quality is DataQuality.COMPLETE


def test_short_position_gains_when_price_falls(make_position):
    vp = value_position(
        make_position(quantity=Decimal("-50"), avg_price=Decimal("20"), market_price=Decimal("18"))
    )
    assert vp.side is Side.SHORT
    assert vp.market_value == Decimal("-900")  # signed: short is negative
    assert vp.unrealised_pl == Decimal("100")  # -50 * (18 - 20)


def test_utilisation_percent(make_position):
    vp = value_position(
        make_position(
            quantity=Decimal("100"), market_price=Decimal("18"), exposure_limit=Decimal("2000")
        )
    )
    assert vp.utilisation_pct == Decimal("90")  # 1800 / 2000 * 100


def test_missing_market_price_propagates_none_not_zero(make_position):
    vp = value_position(make_position(market_price=None))
    assert vp.market_value is None
    assert vp.unrealised_pl is None
    assert vp.utilisation_pct is None
    assert vp.data_quality is DataQuality.INCOMPLETE


def test_missing_var_makes_incomplete(make_position):
    vp = value_position(make_position(var_1d=None))
    assert vp.data_quality is DataQuality.INCOMPLETE
    # value-based fields still compute because market_price is present
    assert vp.market_value == Decimal("1200")


def test_flat_position(make_position):
    vp = value_position(make_position(quantity=Decimal("0")))
    assert vp.side is Side.FLAT
    assert vp.market_value == Decimal("0")
