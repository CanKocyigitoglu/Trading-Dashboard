"""Central configuration for the trading-risk prototype.

All alert thresholds and business-facing labels live here so they can be
reviewed and adjusted in one place. Calculation logic lives in ``metrics.py``
and ``alerts.py``; this module holds only constants and labels.
"""

from __future__ import annotations

from pathlib import Path

# --- Data location ---------------------------------------------------------

DATA_FILE = Path(__file__).resolve().parent.parent / "data" / "positions.csv"

# Raw columns that must be present and non-missing for a position to be fully
# valued. ``market_price`` and ``var_1d`` are intentionally allowed to be
# missing in the sample data to demonstrate the data-quality alert.
REQUIRED_VALUE_COLUMNS = ("market_price", "var_1d")


# --- Alert thresholds ------------------------------------------------------
# These are prototype demonstration thresholds, not authoritative risk limits.

# Utilisation = abs(market_value) / exposure_limit, expressed as a percentage.
UTILISATION_BREACH_PCT = 100.0  # at or above limit -> High severity
UTILISATION_WARN_PCT = 85.0  # approaching limit -> Medium severity

# A position whose unrealised P/L falls below this (USD) is flagged.
PL_LOSS_THRESHOLD_USD = -150_000.0

# A position whose supplied 1-day VaR exceeds this (USD) is flagged.
VAR_LIMIT_USD = 200_000.0

# The dataset is considered stale if its timestamp is older than this.
STALENESS_MAX_AGE_HOURS = 24

# Severity labels (ordered most to least urgent) used for sorting/display.
SEVERITY_HIGH = "High"
SEVERITY_MEDIUM = "Medium"
SEVERITY_ORDER = (SEVERITY_HIGH, SEVERITY_MEDIUM)


# --- Business labels -------------------------------------------------------
# Human-readable column headings used in the presentation layer. Raw column
# names are never shown directly to the user.

REPORTING_CURRENCY = "USD"

COLUMN_LABELS = {
    "desk": "Desk",
    "trader": "Trader",
    "instrument": "Instrument",
    "commodity": "Commodity",
    "unit": "Unit",
    "quantity": "Quantity (signed)",
    "side": "Side",
    "avg_price": "Avg Price",
    "market_price": "Market Price",
    "currency": "Currency",
    "market_value": f"Market Value ({REPORTING_CURRENCY})",
    "unrealised_pl": f"Unrealised P/L ({REPORTING_CURRENCY})",
    "var_1d": f"1-Day VaR ({REPORTING_CURRENCY})",
    "exposure_limit": f"Exposure Limit ({REPORTING_CURRENCY})",
    "utilisation_pct": "Utilisation %",
}
