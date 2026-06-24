"""Presentation helpers for formatting values for display.

Shared by the alerts module (to build human-readable reasons) and the
Streamlit app (to format tables and cards). Rounding happens here, at the
presentation boundary only -- never in the calculation layer.
"""

from __future__ import annotations

import math

# Shown wherever a value is genuinely missing, to distinguish it from zero.
MISSING = "—"


def _is_missing(value: float | int | None) -> bool:
    return value is None or (isinstance(value, float) and math.isnan(value))


def money(value: float | int | None, currency: str = "USD") -> str:
    """Format a currency amount with thousands separators, no decimals."""
    if _is_missing(value):
        return MISSING
    return f"{currency} {value:,.0f}"


def percent(value: float | int | None, decimals: int = 1) -> str:
    """Format a percentage value (already expressed in percent units)."""
    if _is_missing(value):
        return MISSING
    return f"{value:,.{decimals}f}%"


def number(value: float | int | None, decimals: int = 0) -> str:
    """Format a plain number with thousands separators."""
    if _is_missing(value):
        return MISSING
    return f"{value:,.{decimals}f}"
