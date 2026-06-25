"""Adapter tests for the Yahoo market source.

These exercise the pure ``normalise_frame`` path with hand-built DataFrames, so
they never touch the network (per the backend test rules).
"""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal

import pandas as pd

from app.adapters import yahoo_market_source as yh

WTI = yh.BY_SYMBOL["WTI"]
WHEAT = yh.BY_SYMBOL["WHEAT"]


def _frame(index: pd.DatetimeIndex, closes: list[float]) -> pd.DataFrame:
    return pd.DataFrame({"Open": closes, "Close": closes}, index=index)


def test_normalise_preserves_value_currency_unit_and_orders_oldest_first():
    index = pd.to_datetime(["2026-06-25T13:00:00Z", "2026-06-25T13:01:00Z", "2026-06-25T13:02:00Z"])
    obs = yh.normalise_frame(WTI, _frame(index, [78.10, 78.25, 78.40]))

    assert [o.source_ts for o in obs] == [
        datetime(2026, 6, 25, 13, 0, tzinfo=UTC),
        datetime(2026, 6, 25, 13, 1, tzinfo=UTC),
        datetime(2026, 6, 25, 13, 2, tzinfo=UTC),
    ]
    assert obs[-1].price == Decimal("78.4")  # exact, from Decimal(str(...))
    assert obs[0].symbol == "WTI"
    assert obs[0].source_symbol == "CL=F"
    assert obs[0].currency == "USD"
    assert obs[0].unit == "bbl"
    assert obs[0].data_quality == "ok"


def test_grains_keep_native_cents_currency():
    index = pd.to_datetime(["2026-06-25T13:00:00Z"])
    obs = yh.normalise_frame(WHEAT, _frame(index, [595.25]))
    assert obs[0].currency == "USc"  # US cents per bushel, not converted
    assert obs[0].unit == "bu"
    assert obs[0].price == Decimal("595.25")


def test_missing_close_is_skipped_not_zeroed():
    index = pd.to_datetime(["2026-06-25T13:00:00Z", "2026-06-25T13:01:00Z"])
    obs = yh.normalise_frame(WTI, _frame(index, [78.10, float("nan")]))
    assert len(obs) == 1
    assert obs[0].source_ts == datetime(2026, 6, 25, 13, 0, tzinfo=UTC)


def test_naive_timestamps_are_treated_as_utc():
    index = pd.DatetimeIndex([datetime(2026, 6, 25, 13, 0)])  # tz-naive
    obs = yh.normalise_frame(WTI, _frame(index, [78.10]))
    assert obs[0].source_ts == datetime(2026, 6, 25, 13, 0, tzinfo=UTC)


def test_tz_aware_index_is_converted_to_utc():
    index = pd.to_datetime(["2026-06-25T09:00:00-04:00"])  # US/Eastern style offset
    obs = yh.normalise_frame(WTI, _frame(index, [78.10]))
    assert obs[0].source_ts == datetime(2026, 6, 25, 13, 0, tzinfo=UTC)


def test_empty_frame_returns_no_observations():
    assert yh.normalise_frame(WTI, pd.DataFrame()) == []
