"""Deterministic alert evaluation for the trading-risk prototype.

Every rule here is a plain numeric/temporal comparison against a threshold
defined in ``config.py``. No model or heuristic is involved -- given the same
data and thresholds, the same alerts always fire.

Each alert records its severity, the affected scope (desk / trader /
instrument), the observed value, the relevant threshold and a plain-English
reason, as required by the project brief.
"""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from . import config, formatting


@dataclass(frozen=True)
class Alert:
    severity: str
    category: str
    desk: str
    trader: str
    instrument: str
    observed: str
    threshold: str
    reason: str


def _position_alerts(row: pd.Series) -> list[Alert]:
    """Evaluate all per-position rules for a single enriched row."""
    found: list[Alert] = []
    desk = str(row["desk"])
    trader = str(row["trader"])
    instrument = str(row["instrument"])

    # 1 & 2. Exposure utilisation against the position limit.
    utilisation = row["utilisation_pct"]
    if pd.notna(utilisation):
        if utilisation >= config.UTILISATION_BREACH_PCT:
            found.append(
                Alert(
                    severity=config.SEVERITY_HIGH,
                    category="Exposure limit",
                    desk=desk,
                    trader=trader,
                    instrument=instrument,
                    observed=formatting.percent(utilisation),
                    threshold=f">= {formatting.percent(config.UTILISATION_BREACH_PCT)}",
                    reason="Gross exposure is at or above the position exposure limit.",
                )
            )
        elif utilisation >= config.UTILISATION_WARN_PCT:
            found.append(
                Alert(
                    severity=config.SEVERITY_MEDIUM,
                    category="Exposure limit",
                    desk=desk,
                    trader=trader,
                    instrument=instrument,
                    observed=formatting.percent(utilisation),
                    threshold=f">= {formatting.percent(config.UTILISATION_WARN_PCT)}",
                    reason="Gross exposure is approaching the position exposure limit.",
                )
            )

    # 3. Unrealised P/L below the configured loss threshold.
    pnl = row["unrealised_pl"]
    if pd.notna(pnl) and pnl < config.PL_LOSS_THRESHOLD_USD:
        found.append(
            Alert(
                severity=config.SEVERITY_HIGH,
                category="P/L",
                desk=desk,
                trader=trader,
                instrument=instrument,
                observed=formatting.money(pnl),
                threshold=f"< {formatting.money(config.PL_LOSS_THRESHOLD_USD)}",
                reason="Unrealised loss is below the configured loss threshold.",
            )
        )

    # 4. Supplied 1-day VaR above the configured VaR limit.
    var_1d = row["var_1d"]
    if pd.notna(var_1d) and var_1d > config.VAR_LIMIT_USD:
        found.append(
            Alert(
                severity=config.SEVERITY_MEDIUM,
                category="VaR",
                desk=desk,
                trader=trader,
                instrument=instrument,
                observed=formatting.money(var_1d),
                threshold=f"> {formatting.money(config.VAR_LIMIT_USD)}",
                reason="Supplied 1-day VaR exceeds the configured VaR limit.",
            )
        )

    # 5. A required input value is missing for this position.
    missing_cols = [c for c in config.REQUIRED_VALUE_COLUMNS if pd.isna(row[c])]
    if missing_cols:
        labels = ", ".join(config.COLUMN_LABELS.get(c, c) for c in missing_cols)
        found.append(
            Alert(
                severity=config.SEVERITY_HIGH,
                category="Data quality",
                desk=desk,
                trader=trader,
                instrument=instrument,
                observed=f"Missing: {labels}",
                threshold="All required values present",
                reason="A required value is missing, so this position cannot be fully valued.",
            )
        )

    return found


def _staleness_alert(timestamp: pd.Timestamp | None, now: pd.Timestamp) -> Alert | None:
    """Flag the dataset if its timestamp is older than the freshness window."""
    if timestamp is None:
        return Alert(
            severity=config.SEVERITY_HIGH,
            category="Staleness",
            desk="All",
            trader="All",
            instrument="All",
            observed=formatting.MISSING,
            threshold=f"<= {config.STALENESS_MAX_AGE_HOURS}h old",
            reason="The dataset has no usable timestamp, so its freshness cannot be confirmed.",
        )

    age_hours = (now - timestamp).total_seconds() / 3600.0
    if age_hours > config.STALENESS_MAX_AGE_HOURS:
        return Alert(
            severity=config.SEVERITY_HIGH,
            category="Staleness",
            desk="All",
            trader="All",
            instrument="All",
            observed=f"{age_hours:,.1f}h old",
            threshold=f"<= {config.STALENESS_MAX_AGE_HOURS}h old",
            reason="Dataset timestamp is older than the configured freshness window.",
        )
    return None


def evaluate_alerts(
    enriched: pd.DataFrame,
    now: pd.Timestamp,
    dataset_timestamp: pd.Timestamp | None,
) -> list[Alert]:
    """Return all triggered alerts, ordered most urgent first.

    ``enriched`` must already contain the derived columns from
    :func:`metrics.enrich_positions`. ``now`` is passed in (rather than read
    from the clock) so the result is deterministic and testable.
    """
    alerts: list[Alert] = []

    stale = _staleness_alert(dataset_timestamp, now)
    if stale is not None:
        alerts.append(stale)

    for _, row in enriched.iterrows():
        alerts.extend(_position_alerts(row))

    severity_rank = {name: index for index, name in enumerate(config.SEVERITY_ORDER)}
    alerts.sort(key=lambda a: (severity_rank.get(a.severity, 99), a.category, a.instrument))
    return alerts


def alerts_to_frame(alerts: list[Alert]) -> pd.DataFrame:
    """Convert alerts to a display DataFrame with business-friendly headings."""
    if not alerts:
        return pd.DataFrame(
            columns=[
                "Severity",
                "Category",
                "Desk",
                "Trader",
                "Instrument",
                "Observed",
                "Threshold",
                "Reason",
            ]
        )
    return pd.DataFrame(
        [
            {
                "Severity": a.severity,
                "Category": a.category,
                "Desk": a.desk,
                "Trader": a.trader,
                "Instrument": a.instrument,
                "Observed": a.observed,
                "Threshold": a.threshold,
                "Reason": a.reason,
            }
            for a in alerts
        ]
    )
