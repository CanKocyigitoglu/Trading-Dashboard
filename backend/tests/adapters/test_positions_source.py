"""Tests for the read-only CSV positions adapter (normalisation)."""

from __future__ import annotations

from datetime import UTC
from decimal import Decimal

import pytest

from app.adapters.positions_source import PositionsSourceError, load_positions

HEADER = (
    "position_id,desk,trader,instrument,commodity,unit,quantity,avg_price,"
    "market_price,currency,var_1d,exposure_limit,as_of"
)


def _write_csv(tmp_path, *rows):
    path = tmp_path / "positions.csv"
    path.write_text("\n".join((HEADER, *rows)) + "\n", encoding="utf-8")
    return path


def test_parses_values_with_exact_precision(tmp_path):
    path = _write_csv(
        tmp_path,
        "P001,Crude Oil,Alice,WTI,WTI Crude,bbl,50000,74.50,78.20,USD,"
        "180000,4500000,2026-06-24T15:30:00Z",
    )
    [p] = load_positions(path)
    assert p.quantity == Decimal("50000")
    assert p.avg_price == Decimal("74.50")  # exact, not 74.5000001
    assert p.market_price == Decimal("78.20")
    assert p.currency == "USD"
    assert p.as_of.tzinfo is not None
    assert p.as_of.utcoffset() == UTC.utcoffset(None)


def test_blank_numeric_becomes_none_not_zero(tmp_path):
    path = _write_csv(
        tmp_path,
        "P014,Ag,Eva,Soybean,Soybean,bu,150000,11.20,,USD,,1600000,2026-06-24T15:30:00Z",
    )
    [p] = load_positions(path)
    assert p.market_price is None
    assert p.var_1d is None


def test_missing_required_field_raises(tmp_path):
    path = _write_csv(
        tmp_path,
        "P001,Crude Oil,Alice,WTI,WTI Crude,bbl,,74.50,78.20,USD,"
        "180000,4500000,2026-06-24T15:30:00Z",
    )
    with pytest.raises(PositionsSourceError):
        load_positions(path)


def test_naive_timestamp_raises(tmp_path):
    path = _write_csv(
        tmp_path,
        "P001,Crude Oil,Alice,WTI,WTI Crude,bbl,50000,74.50,78.20,USD,"
        "180000,4500000,2026-06-24T15:30:00",
    )
    with pytest.raises(PositionsSourceError):
        load_positions(path)


def test_missing_file_raises(tmp_path):
    with pytest.raises(PositionsSourceError):
        load_positions(tmp_path / "does_not_exist.csv")
