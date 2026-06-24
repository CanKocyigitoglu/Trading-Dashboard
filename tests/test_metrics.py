"""Tests for the financial calculation layer."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from src import metrics


def test_enrich_signs_for_long_and_short(make_positions):
    df = make_positions(
        [
            {"quantity": 100, "avg_price": 10, "market_price": 12, "exposure_limit": 2_000},
            {"quantity": -50, "avg_price": 20, "market_price": 18, "exposure_limit": 1_000},
        ]
    )
    enriched = metrics.enrich_positions(df)

    assert enriched.loc[0, "side"] == "Long"
    assert enriched.loc[1, "side"] == "Short"

    assert enriched.loc[0, "market_value"] == 1_200
    assert enriched.loc[1, "market_value"] == -900

    assert enriched.loc[0, "unrealised_pl"] == 200
    # Short position gains when the price falls: -50 * (18 - 20) = 100.
    assert enriched.loc[1, "unrealised_pl"] == 100

    assert enriched.loc[1, "utilisation_pct"] == pytest.approx(90.0)


def test_missing_market_price_propagates_nan_not_zero(make_positions):
    df = make_positions([{"quantity": 10, "market_price": np.nan, "var_1d": np.nan}])
    enriched = metrics.enrich_positions(df)

    assert pd.isna(enriched.loc[0, "market_value"])
    assert pd.isna(enriched.loc[0, "unrealised_pl"])
    assert pd.isna(enriched.loc[0, "utilisation_pct"])


def test_enrich_does_not_mutate_input(make_positions):
    df = make_positions([{"quantity": 100}])
    metrics.enrich_positions(df)
    assert "market_value" not in df.columns


def test_portfolio_kpis_exclude_missing_values(make_positions):
    df = make_positions(
        [
            {"quantity": 100, "avg_price": 10, "market_price": 12, "var_1d": 50},
            {"quantity": -50, "avg_price": 20, "market_price": 18, "var_1d": 80},
            {"quantity": 10, "avg_price": 5, "market_price": np.nan, "var_1d": np.nan},
        ]
    )
    enriched = metrics.enrich_positions(df)
    kpis = metrics.portfolio_kpis(enriched)

    assert kpis.net_exposure == 300  # 1200 + (-900); missing row excluded
    assert kpis.gross_exposure == 2_100  # 1200 + 900
    assert kpis.total_unrealised_pl == 300  # 200 + 100
    assert kpis.total_var_1d == 130  # 50 + 80; missing var not counted as zero
    assert kpis.position_count == 3
    assert kpis.incomplete_position_count == 1


def test_aggregate_exposure_sorted_descending(make_positions):
    df = make_positions(
        [
            {"desk": "Crude Oil", "quantity": 100, "market_price": 12},  # 1200
            {"desk": "Metals", "quantity": 100, "market_price": 50},  # 5000
        ]
    )
    enriched = metrics.enrich_positions(df)
    agg = metrics.aggregate_exposure(enriched, "desk")

    assert list(agg["desk"]) == ["Metals", "Crude Oil"]
    assert agg.loc[0, "gross_exposure"] == 5_000


def test_aggregate_pl_groups_and_sums(make_positions):
    df = make_positions(
        [
            {"trader": "Alice Chen", "quantity": 100, "avg_price": 10, "market_price": 12},  # +200
            {"trader": "Alice Chen", "quantity": 100, "avg_price": 10, "market_price": 11},  # +100
            {"trader": "Bob Martin", "quantity": 100, "avg_price": 10, "market_price": 8},  # -200
        ]
    )
    enriched = metrics.enrich_positions(df)
    agg = metrics.aggregate_pl(enriched, "trader")

    pl_by_trader = dict(zip(agg["trader"], agg["unrealised_pl"], strict=True))
    assert pl_by_trader["Alice Chen"] == 300
    assert pl_by_trader["Bob Martin"] == -200
