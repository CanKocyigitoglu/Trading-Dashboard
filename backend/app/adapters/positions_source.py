"""Read-only positions source adapter (CSV).

Reads a bounded sample CSV into typed :class:`Position` objects. The adapter is
read-only and replaceable: a later slice can swap this for a different upstream
source without changing the domain, alert or API layers.

Numbers are parsed from their original string form into ``Decimal`` so source
precision is preserved, and blank cells become ``None`` (unavailable) rather
than zero.
"""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path

import pandas as pd

from ..domain.positions import Position

EXPECTED_COLUMNS = (
    "position_id",
    "desk",
    "trader",
    "instrument",
    "commodity",
    "unit",
    "quantity",
    "avg_price",
    "market_price",
    "currency",
    "var_1d",
    "exposure_limit",
    "as_of",
)


class PositionsSourceError(ValueError):
    """Raised when the source data cannot be read or is malformed."""


def _required_decimal(raw: str, field: str, position_id: str) -> Decimal:
    if raw == "":
        raise PositionsSourceError(f"{position_id}: required field '{field}' is empty")
    try:
        return Decimal(raw)
    except InvalidOperation as exc:
        raise PositionsSourceError(f"{position_id}: invalid number for '{field}': {raw!r}") from exc


def _optional_decimal(raw: str, field: str, position_id: str) -> Decimal | None:
    if raw == "":
        return None  # unavailable, kept distinct from zero
    try:
        return Decimal(raw)
    except InvalidOperation as exc:
        raise PositionsSourceError(f"{position_id}: invalid number for '{field}': {raw!r}") from exc


def _timestamp(raw: str, position_id: str) -> datetime:
    try:
        parsed = datetime.fromisoformat(raw.replace("Z", "+00:00"))
    except ValueError as exc:
        raise PositionsSourceError(f"{position_id}: invalid timestamp: {raw!r}") from exc
    if parsed.tzinfo is None:
        raise PositionsSourceError(f"{position_id}: timestamp must include a timezone: {raw!r}")
    return parsed.astimezone(UTC)


def load_positions(path: Path | str) -> list[Position]:
    """Load and validate positions from the CSV at ``path`` (read-only)."""
    csv_path = Path(path)
    if not csv_path.exists():
        raise PositionsSourceError(f"Positions source not found: {csv_path}")

    # dtype=str + keep_default_na=False keeps every cell as its raw string, so a
    # blank stays "" (unavailable) and is never coerced to NaN/0 by pandas.
    frame = pd.read_csv(csv_path, dtype=str, keep_default_na=False)

    missing = [c for c in EXPECTED_COLUMNS if c not in frame.columns]
    if missing:
        raise PositionsSourceError(f"Source is missing columns: {missing}")

    positions: list[Position] = []
    for record in frame.to_dict(orient="records"):
        position_id = str(record["position_id"])
        positions.append(
            Position(
                position_id=position_id,
                desk=str(record["desk"]),
                trader=str(record["trader"]),
                instrument=str(record["instrument"]),
                commodity=str(record["commodity"]),
                unit=str(record["unit"]),
                currency=str(record["currency"]),
                quantity=_required_decimal(record["quantity"], "quantity", position_id),
                avg_price=_required_decimal(record["avg_price"], "avg_price", position_id),
                market_price=_optional_decimal(record["market_price"], "market_price", position_id),
                var_1d=_optional_decimal(record["var_1d"], "var_1d", position_id),
                exposure_limit=_required_decimal(
                    record["exposure_limit"], "exposure_limit", position_id
                ),
                as_of=_timestamp(record["as_of"], position_id),
            )
        )
    return positions
