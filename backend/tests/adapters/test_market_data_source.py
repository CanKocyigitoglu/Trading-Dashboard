"""Tests for the synthetic market-data adapter.

The generator must be fully deterministic given a fixed ``now`` (so tests and
repeated requests agree) while still producing a moving series.
"""

from __future__ import annotations

from datetime import UTC, datetime

from app.adapters import market_data_source as mkt

FIXED_NOW = datetime(2026, 6, 25, 12, 0, 7, tzinfo=UTC)  # mid-bucket on purpose


def test_overview_is_reproducible_for_a_fixed_now():
    first = mkt.build_overview(FIXED_NOW, 900)
    second = mkt.build_overview(FIXED_NOW, 900)
    assert first == second  # guards against hash() salting / RNG state leakage


def test_overview_covers_the_whole_universe_and_is_labelled_synthetic():
    overview = mkt.build_overview(FIXED_NOW, 900)
    assert overview.synthetic is True
    symbols = {q.symbol for q in overview.quotes}
    assert symbols == {c.symbol for c in mkt.COMMODITY_UNIVERSE}


def test_quote_series_has_window_length_and_bucket_aligned_utc_times():
    quote = mkt.build_overview(FIXED_NOW, 900).quotes[0]
    assert len(quote.series) == mkt.WINDOW

    # as_of is the start of the current bucket, not the raw (mid-bucket) now.
    current = mkt.bucket_index_for(FIXED_NOW)
    assert quote.as_of == datetime.fromtimestamp(current * mkt.BUCKET_SECONDS, tz=UTC)
    assert quote.as_of.tzinfo is not None
    assert quote.series[-1].t == quote.as_of

    # Points are spaced one bucket apart, in UTC.
    gap = quote.series[1].t - quote.series[0].t
    assert gap.total_seconds() == mkt.BUCKET_SECONDS


def test_change_matches_last_two_points():
    quote = mkt.build_overview(FIXED_NOW, 900).quotes[0]
    assert quote.last_price == quote.series[-1].price
    assert quote.previous_price == quote.series[-2].price
    assert quote.change == round(quote.last_price - quote.previous_price, 4)
    expected_pct = round(quote.change / quote.previous_price * 100, 4)
    assert quote.change_pct == expected_pct


def test_series_actually_moves():
    quote = mkt.build_overview(FIXED_NOW, 900).quotes[0]
    prices = {p.price for p in quote.series}
    assert len(prices) > 1  # not a flat line


def test_prices_stay_within_the_synthetic_volatility_band():
    overview = mkt.build_overview(FIXED_NOW, 900)
    by_symbol = {c.symbol: c for c in mkt.COMMODITY_UNIVERSE}
    for quote in overview.quotes:
        commodity = by_symbol[quote.symbol]
        band = commodity.anchor * commodity.vol_pct
        for point in quote.series:
            assert abs(point.price - commodity.anchor) <= band + 1e-3  # +rounding slack
