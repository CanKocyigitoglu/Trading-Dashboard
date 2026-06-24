"""Loading and typing of the prototype positions dataset.

This module is responsible only for reading the CSV and applying correct
types. It does not compute any financial metrics and it does not fill or
modify missing values -- missing inputs are preserved as NaN/NaT so that
downstream logic can treat "missing" differently from "zero".
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from . import config

# Columns that must hold numbers. Anything non-numeric or blank becomes NaN
# rather than being coerced to zero.
NUMERIC_COLUMNS = (
    "quantity",
    "avg_price",
    "market_price",
    "var_1d",
    "exposure_limit",
)


def load_positions(path: Path | str | None = None) -> pd.DataFrame:
    """Load the positions CSV into a typed DataFrame.

    Missing numeric values are kept as NaN and ``as_of`` is parsed to a
    timestamp. The returned frame is a fresh object; the source file is never
    written back to.
    """
    csv_path = Path(path) if path is not None else config.DATA_FILE
    if not csv_path.exists():
        raise FileNotFoundError(f"Positions data file not found: {csv_path}")

    frame = pd.read_csv(csv_path)

    for column in NUMERIC_COLUMNS:
        frame[column] = pd.to_numeric(frame[column], errors="coerce")

    frame["as_of"] = pd.to_datetime(frame["as_of"], errors="coerce")

    return frame


def dataset_timestamp(positions: pd.DataFrame) -> pd.Timestamp | None:
    """Return the most recent ``as_of`` timestamp, or None if unavailable."""
    if "as_of" not in positions or positions["as_of"].isna().all():
        return None
    return positions["as_of"].max()
