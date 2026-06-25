"""Tests for portfolio aggregation."""

from __future__ import annotations

from decimal import Decimal

import pytest

from app.domain.portfolio import CurrencyAggregationError, summarise
from app.domain.positions import value_position


def test_summary_excludes_missing_values_not_as_zero(make_position):
    valued = [
        value_position(
            make_position(
                position_id="P1",
                quantity=Decimal("100"),
                market_price=Decimal("12"),
                var_1d=Decimal("50"),
            )
        ),
        value_position(
            make_position(
                position_id="P2",
                quantity=Decimal("-50"),
                avg_price=Decimal("20"),
                market_price=Decimal("18"),
                var_1d=Decimal("80"),
            )
        ),
        value_position(
            make_position(position_id="P3", quantity=Decimal("10"), market_price=None, var_1d=None)
        ),
    ]
    summary = summarise(valued)

    assert summary.currency == "USD"
    assert summary.net_exposure == Decimal("300")  # 1200 + (-900); P3 excluded
    assert summary.gross_exposure == Decimal("2100")  # 1200 + 900
    assert summary.total_unrealised_pl == Decimal("300")  # 200 + 100
    assert summary.total_var_1d_illustrative == Decimal("130")  # 50 + 80, P3 missing not zero
    assert summary.position_count == 3
    assert summary.incomplete_position_count == 1


def test_refuses_to_aggregate_across_currencies(make_position):
    valued = [
        value_position(make_position(position_id="P1", currency="USD")),
        value_position(make_position(position_id="P2", currency="EUR")),
    ]
    with pytest.raises(CurrencyAggregationError):
        summarise(valued)


def test_empty_summary_is_rejected():
    with pytest.raises(ValueError):
        summarise([])
