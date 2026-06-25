"""Tests for deterministic alert rules, including threshold boundaries."""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal

from app.alerts import rules
from app.alerts.rules import Severity
from app.domain.positions import value_position

NOW = datetime(2026, 6, 24, 16, 0, tzinfo=UTC)  # 0.5h after sample as_of
STALE_NOW = datetime(2026, 6, 26, 16, 0, tzinfo=UTC)  # > 24h after as_of


def _evaluate(positions, now=NOW):
    return rules.evaluate([value_position(p) for p in positions], now=now)


def _rule_ids(alerts):
    return {a.rule_id for a in alerts}


# --- Utilisation thresholds (warn 85%, breach 100%) ------------------------


def test_utilisation_above_breach_is_high(make_position):
    # 100 * 25 = 2500 / 2000 = 125%
    alerts = _evaluate([make_position(quantity=Decimal("100"), market_price=Decimal("25"))])
    breach = next(a for a in alerts if a.rule_id == "EXPOSURE_UTILISATION_BREACH")
    assert breach.severity is Severity.HIGH


def test_utilisation_exactly_at_breach_is_high(make_position):
    # 100 * 20 = 2000 / 2000 = 100% exactly
    alerts = _evaluate([make_position(quantity=Decimal("100"), market_price=Decimal("20"))])
    assert "EXPOSURE_UTILISATION_BREACH" in _rule_ids(alerts)


def test_utilisation_exactly_at_warn_is_medium(make_position):
    # 100 * 17 = 1700 / 2000 = 85% exactly
    alerts = _evaluate([make_position(quantity=Decimal("100"), market_price=Decimal("17"))])
    assert "EXPOSURE_UTILISATION_WARN" in _rule_ids(alerts)


def test_utilisation_just_below_warn_has_no_exposure_alert(make_position):
    # 100 * 16.9 = 1690 / 2000 = 84.5%
    alerts = _evaluate([make_position(quantity=Decimal("100"), market_price=Decimal("16.9"))])
    assert not {r for r in _rule_ids(alerts) if r.startswith("EXPOSURE_UTILISATION")}


# --- P/L loss threshold (-150,000) -----------------------------------------


def test_pnl_exactly_at_threshold_does_not_trigger(make_position):
    # 100000 * (8.5 - 10) = -150000 exactly; rule is strictly less-than
    alerts = _evaluate(
        [
            make_position(
                quantity=Decimal("100000"),
                avg_price=Decimal("10"),
                market_price=Decimal("8.5"),
                exposure_limit=Decimal("999999999"),
            )
        ]
    )
    assert "PNL_LOSS" not in _rule_ids(alerts)


def test_pnl_just_below_threshold_is_high(make_position):
    # 100000 * (8.49 - 10) = -151000
    alerts = _evaluate(
        [
            make_position(
                quantity=Decimal("100000"),
                avg_price=Decimal("10"),
                market_price=Decimal("8.49"),
                exposure_limit=Decimal("999999999"),
            )
        ]
    )
    pnl = next(a for a in alerts if a.rule_id == "PNL_LOSS")
    assert pnl.severity is Severity.HIGH


# --- VaR limit (200,000) ---------------------------------------------------


def test_var_exactly_at_limit_does_not_trigger(make_position):
    alerts = _evaluate(
        [make_position(var_1d=Decimal("200000"), exposure_limit=Decimal("999999999"))]
    )
    assert "VAR_LIMIT" not in _rule_ids(alerts)


def test_var_above_limit_is_medium(make_position):
    alerts = _evaluate(
        [make_position(var_1d=Decimal("200001"), exposure_limit=Decimal("999999999"))]
    )
    var = next(a for a in alerts if a.rule_id == "VAR_LIMIT")
    assert var.severity is Severity.MEDIUM


# --- Missing values --------------------------------------------------------


def test_missing_required_value_only_fires_data_alert(make_position):
    alerts = _evaluate([make_position(market_price=None, var_1d=None)])
    position_alerts = {a.rule_id for a in alerts if a.entity_type == "position"}
    assert position_alerts == {"DATA_MISSING_REQUIRED"}
    data_alert = next(a for a in alerts if a.rule_id == "DATA_MISSING_REQUIRED")
    assert data_alert.severity is Severity.HIGH
    assert data_alert.detail_reference == "P001"


# --- Staleness -------------------------------------------------------------


def test_fresh_dataset_has_no_staleness_alert(make_position):
    assert "DATA_STALE" not in _rule_ids(_evaluate([make_position(market_price=Decimal("12"))]))


def test_stale_dataset_is_high(make_position):
    alerts = _evaluate([make_position(market_price=Decimal("12"))], now=STALE_NOW)
    stale = next(a for a in alerts if a.rule_id == "DATA_STALE")
    assert stale.severity is Severity.HIGH
    assert stale.entity_type == "dataset"


# --- Required alert fields, dedup and ordering -----------------------------


def test_alert_carries_required_fields(make_position):
    alert = next(
        a
        for a in _evaluate([make_position(quantity=Decimal("100"), market_price=Decimal("25"))])
        if a.rule_id == "EXPOSURE_UTILISATION_BREACH"
    )
    assert alert.instrument == "WTI Crude Futures"
    assert alert.observed and alert.threshold and alert.reason
    assert alert.evaluation_timestamp == NOW
    assert alert.status == "open"


def test_alerts_sorted_high_before_medium(make_position):
    alerts = _evaluate(
        [
            make_position(
                position_id="P1",
                quantity=Decimal("100000"),
                avg_price=Decimal("10"),
                market_price=Decimal("8"),
                exposure_limit=Decimal("999999999"),
            ),
            make_position(position_id="P2", quantity=Decimal("100"), market_price=Decimal("18")),
        ]
    )
    severities = [a.severity for a in alerts]
    rank = {s: i for i, s in enumerate(rules.SEVERITY_ORDER)}
    assert severities == sorted(severities, key=lambda s: rank[s])


def test_duplicate_alerts_are_removed(make_position):
    # Same valued position passed twice would yield identical (rule_id, ref) pairs.
    p = make_position(quantity=Decimal("100"), market_price=Decimal("25"))
    valued = [value_position(p), value_position(p)]
    alerts = rules.evaluate(valued, now=NOW)
    breaches = [a for a in alerts if a.rule_id == "EXPOSURE_UTILISATION_BREACH"]
    assert len(breaches) == 1
