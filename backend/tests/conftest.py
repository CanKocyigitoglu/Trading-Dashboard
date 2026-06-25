"""Shared fixtures: a factory for building Position objects in tests."""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal

import pytest

from app.domain.positions import Position

_BASE = {
    "position_id": "P001",
    "desk": "Crude Oil",
    "trader": "Alice Chen",
    "instrument": "WTI Crude Futures",
    "commodity": "WTI Crude",
    "unit": "bbl",
    "currency": "USD",
    "quantity": Decimal("100"),
    "avg_price": Decimal("10"),
    "market_price": Decimal("12"),
    "var_1d": Decimal("50"),
    "exposure_limit": Decimal("2000"),
    "as_of": datetime(2026, 6, 24, 15, 30, tzinfo=UTC),
}


@pytest.fixture
def make_position():
    def _make(**overrides):
        return Position(**{**_BASE, **overrides})

    return _make
