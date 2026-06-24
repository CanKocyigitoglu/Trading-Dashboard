"""Tests for the deterministic alert rules."""

from __future__ import annotations

import numpy as np
import pandas as pd

from src import alerts, config, metrics

NOW = pd.Timestamp("2026-06-24T17:00:00")
FRESH_TS = pd.Timestamp("2026-06-24T16:30:00")  # 0.5h old
STALE_TS = pd.Timestamp("2026-06-20T16:30:00")  # > 24h old


def _evaluate(df, now=NOW, dataset_timestamp=FRESH_TS):
    enriched = metrics.enrich_positions(df)
    return alerts.evaluate_alerts(enriched, now=now, dataset_timestamp=dataset_timestamp)


def _categories(found):
    return {(a.category, a.severity) for a in found}


def test_utilisation_breach_is_high(make_positions):
    # market_value = 100 * 25 = 2500, limit 2000 -> 125% utilisation.
    df = make_positions([{"quantity": 100, "market_price": 25, "exposure_limit": 2_000}])
    assert ("Exposure limit", config.SEVERITY_HIGH) in _categories(_evaluate(df))


def test_utilisation_warning_is_medium(make_positions):
    # 100 * 18 = 1800, limit 2000 -> 90% utilisation (warn band).
    df = make_positions([{"quantity": 100, "market_price": 18, "exposure_limit": 2_000}])
    assert ("Exposure limit", config.SEVERITY_MEDIUM) in _categories(_evaluate(df))


def test_no_exposure_alert_below_warning(make_positions):
    # 100 * 12 = 1200, limit 2000 -> 60% utilisation (no alert).
    df = make_positions([{"quantity": 100, "market_price": 12, "exposure_limit": 2_000}])
    categories = {a.category for a in _evaluate(df)}
    assert "Exposure limit" not in categories


def test_pl_loss_below_threshold_is_high(make_positions):
    # 100000 * (8 - 10) = -200000, below the -150000 loss threshold.
    df = make_positions(
        [
            {
                "quantity": 100_000,
                "avg_price": 10,
                "market_price": 8,
                "exposure_limit": 50_000_000,  # large so no exposure alert
            }
        ]
    )
    assert ("P/L", config.SEVERITY_HIGH) in _categories(_evaluate(df))


def test_var_above_limit_is_medium(make_positions):
    df = make_positions([{"market_price": 12, "var_1d": 250_000, "exposure_limit": 50_000_000}])
    assert ("VaR", config.SEVERITY_MEDIUM) in _categories(_evaluate(df))


def test_missing_required_value_is_high(make_positions):
    df = make_positions([{"market_price": np.nan, "var_1d": np.nan}])
    found = _evaluate(df)
    assert ("Data quality", config.SEVERITY_HIGH) in _categories(found)
    # A missing value must not also fire exposure / P/L / VaR alerts.
    assert {a.category for a in found} <= {"Data quality"}


def test_stale_dataset_is_high(make_positions):
    df = make_positions([{"market_price": 12}])
    assert ("Staleness", config.SEVERITY_HIGH) in _categories(
        _evaluate(df, dataset_timestamp=STALE_TS)
    )


def test_fresh_dataset_has_no_staleness_alert(make_positions):
    df = make_positions([{"market_price": 12}])
    assert "Staleness" not in {a.category for a in _evaluate(df)}


def test_missing_timestamp_is_high(make_positions):
    df = make_positions([{"market_price": 12}])
    assert ("Staleness", config.SEVERITY_HIGH) in _categories(_evaluate(df, dataset_timestamp=None))


def test_alerts_sorted_high_before_medium(make_positions):
    df = make_positions(
        [
            # High: large unrealised loss.
            {"quantity": 100_000, "avg_price": 10, "market_price": 8, "exposure_limit": 50_000_000},
            # Medium: utilisation warning at 90%.
            {"quantity": 100, "market_price": 18, "exposure_limit": 2_000},
        ]
    )
    severities = [a.severity for a in _evaluate(df)]
    rank = {name: i for i, name in enumerate(config.SEVERITY_ORDER)}
    assert severities == sorted(severities, key=lambda s: rank[s])
    assert severities[0] == config.SEVERITY_HIGH


def test_alert_carries_scope_and_reason(make_positions):
    df = make_positions([{"instrument": "WTI Crude Futures", "quantity": 100, "market_price": 25}])
    breach = next(a for a in _evaluate(df) if a.category == "Exposure limit")
    assert breach.instrument == "WTI Crude Futures"
    assert breach.reason  # non-empty plain-English reason
    assert breach.observed != config.SEVERITY_HIGH  # observed is a value, not a label


def test_alerts_to_frame_empty_has_columns():
    frame = alerts.alerts_to_frame([])
    assert frame.empty
    assert "Severity" in frame.columns and "Reason" in frame.columns
