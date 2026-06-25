"""Alert thresholds for the trading-risk slice.

Thresholds live in backend configuration (never in frontend components), so a
single place governs when an alert fires. These are prototype demonstration
values; a later slice can load them from ``ALERT_CONFIG_PATH`` or persisted
alert rules without changing the evaluation logic.
"""

from __future__ import annotations

from decimal import Decimal

# Utilisation = gross exposure / exposure limit, as a percentage.
UTILISATION_BREACH_PCT = Decimal("100")  # at or above limit -> high
UTILISATION_WARN_PCT = Decimal("85")  # approaching limit -> medium

# A position whose unrealised P/L falls below this (reporting currency) is high.
PNL_LOSS_THRESHOLD = Decimal("-150000")

# A position whose supplied 1-day VaR exceeds this (reporting currency) is medium.
VAR_LIMIT = Decimal("200000")

# The dataset is stale if its source timestamp is older than this at evaluation.
STALENESS_MAX_AGE_HOURS = 24
