"""Deterministic alert evaluation.

Every rule here is a plain numeric or temporal comparison against a threshold
from :mod:`app.alerts.config`. No model or heuristic is involved: given the
same valued positions, the same evaluation time and the same thresholds, the
same alerts always fire.

Each alert records the fields required for an explainable, actionable alert:
rule id, severity, affected entity, observed value, threshold/baseline,
evaluation timestamp, plain-English reason, a detail reference for drill-down,
and a status.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from decimal import Decimal
from enum import StrEnum

from ..domain.positions import DataQuality, ValuedPosition
from . import config


class Severity(StrEnum):
    HIGH = "high"
    MEDIUM = "medium"


SEVERITY_ORDER = (Severity.HIGH, Severity.MEDIUM)


@dataclass(frozen=True)
class Alert:
    rule_id: str
    severity: Severity
    entity_type: str  # "position" or "dataset"
    desk: str | None
    trader: str | None
    instrument: str | None
    observed: str
    threshold: str
    evaluation_timestamp: datetime
    reason: str
    detail_reference: str | None  # e.g. position_id, for drill-down
    status: str = "open"


def _money(value: Decimal, currency: str) -> str:
    return f"{currency} {value:,.0f}"


def _pct(value: Decimal) -> str:
    return f"{value:.1f}%"


def _position_alerts(vp: ValuedPosition, now: datetime) -> list[Alert]:
    p = vp.position
    found: list[Alert] = []

    def make(rule_id: str, severity: Severity, observed: str, threshold: str, reason: str) -> Alert:
        return Alert(
            rule_id=rule_id,
            severity=severity,
            entity_type="position",
            desk=p.desk,
            trader=p.trader,
            instrument=p.instrument,
            observed=observed,
            threshold=threshold,
            evaluation_timestamp=now,
            reason=reason,
            detail_reference=p.position_id,
        )

    # Exposure utilisation against the position limit (breach takes priority).
    if vp.utilisation_pct is not None:
        if vp.utilisation_pct >= config.UTILISATION_BREACH_PCT:
            found.append(
                make(
                    "EXPOSURE_UTILISATION_BREACH",
                    Severity.HIGH,
                    _pct(vp.utilisation_pct),
                    f">= {_pct(config.UTILISATION_BREACH_PCT)}",
                    "Gross exposure is at or above the position exposure limit.",
                )
            )
        elif vp.utilisation_pct >= config.UTILISATION_WARN_PCT:
            found.append(
                make(
                    "EXPOSURE_UTILISATION_WARN",
                    Severity.MEDIUM,
                    _pct(vp.utilisation_pct),
                    f">= {_pct(config.UTILISATION_WARN_PCT)}",
                    "Gross exposure is approaching the position exposure limit.",
                )
            )

    # Unrealised P/L below the configured loss threshold.
    if vp.unrealised_pl is not None and vp.unrealised_pl < config.PNL_LOSS_THRESHOLD:
        found.append(
            make(
                "PNL_LOSS",
                Severity.HIGH,
                _money(vp.unrealised_pl, p.currency),
                f"< {_money(config.PNL_LOSS_THRESHOLD, p.currency)}",
                "Unrealised loss is below the configured loss threshold.",
            )
        )

    # Supplied 1-day VaR above the configured VaR limit.
    if p.var_1d is not None and p.var_1d > config.VAR_LIMIT:
        found.append(
            make(
                "VAR_LIMIT",
                Severity.MEDIUM,
                _money(p.var_1d, p.currency),
                f"> {_money(config.VAR_LIMIT, p.currency)}",
                "Supplied 1-day VaR exceeds the configured VaR limit.",
            )
        )

    # A required input value is missing.
    if vp.data_quality is DataQuality.INCOMPLETE:
        missing = [name for name in ("market_price", "var_1d") if getattr(p, name) is None]
        found.append(
            make(
                "DATA_MISSING_REQUIRED",
                Severity.HIGH,
                f"missing: {', '.join(missing)}",
                "all required values present",
                "A required value is missing, so this position cannot be fully valued.",
            )
        )

    return found


def _staleness_alert(source_timestamp: datetime, now: datetime) -> Alert | None:
    age = now - source_timestamp
    if age > timedelta(hours=config.STALENESS_MAX_AGE_HOURS):
        hours = age.total_seconds() / 3600.0
        return Alert(
            rule_id="DATA_STALE",
            severity=Severity.HIGH,
            entity_type="dataset",
            desk=None,
            trader=None,
            instrument=None,
            observed=f"{hours:,.1f}h old",
            threshold=f"<= {config.STALENESS_MAX_AGE_HOURS}h old",
            evaluation_timestamp=now,
            reason="Dataset source timestamp is older than the configured freshness window.",
            detail_reference=None,
        )
    return None


def _deduplicate(alerts: list[Alert]) -> list[Alert]:
    """Drop exact (rule_id, detail_reference) repeats as a safeguard."""
    seen: set[tuple[str, str | None]] = set()
    unique: list[Alert] = []
    for alert in alerts:
        key = (alert.rule_id, alert.detail_reference)
        if key not in seen:
            seen.add(key)
            unique.append(alert)
    return unique


def evaluate(valued: list[ValuedPosition], now: datetime) -> list[Alert]:
    """Return all triggered alerts, deduplicated and ordered most urgent first.

    ``now`` is supplied (not read from the clock) so evaluation is deterministic
    and testable. The dataset staleness check uses the most recent source
    timestamp across the supplied positions.
    """
    alerts: list[Alert] = []

    if valued:
        source_timestamp = max(vp.position.as_of for vp in valued)
        stale = _staleness_alert(source_timestamp, now)
        if stale is not None:
            alerts.append(stale)

    for vp in valued:
        alerts.extend(_position_alerts(vp, now))

    alerts = _deduplicate(alerts)
    rank = {sev: i for i, sev in enumerate(SEVERITY_ORDER)}
    alerts.sort(key=lambda a: (rank[a.severity], a.rule_id, a.instrument or ""))
    return alerts
