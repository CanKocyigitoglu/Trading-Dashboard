"""Shared test fixtures.

Provides a small factory for building positions DataFrames with the same
schema the loader produces, so individual tests only specify the fields that
matter to them.
"""

from __future__ import annotations

import pandas as pd
import pytest

_BASE_ROW = {
    "desk": "Crude Oil",
    "trader": "Alice Chen",
    "instrument": "WTI Crude Futures",
    "commodity": "WTI Crude",
    "unit": "bbl",
    "quantity": 100.0,
    "avg_price": 10.0,
    "market_price": 12.0,
    "currency": "USD",
    "var_1d": 50.0,
    "exposure_limit": 2_000.0,
    "as_of": pd.Timestamp("2026-06-24T16:30:00"),
}


@pytest.fixture
def make_positions():
    """Return a factory: pass a list of partial row dicts, get a DataFrame."""

    def _make(rows: list[dict]) -> pd.DataFrame:
        return pd.DataFrame([{**_BASE_ROW, **row} for row in rows])

    return _make
