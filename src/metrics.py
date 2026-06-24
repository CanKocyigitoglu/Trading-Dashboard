"""Financial calculations for the trading-risk prototype.

These functions are deliberately pure: they take a positions DataFrame and
return new data without touching Streamlit or the source file. Keeping them
here (separate from presentation) makes them straightforward to unit test.

Sign convention
---------------
``quantity`` is signed: a long position is positive, a short position is
negative. Therefore::

    market_value  = quantity * market_price          (signed)
    unrealised_pl = quantity * (market_price - avg_price)

A short position gains when the market price falls, which the signed formula
handles automatically.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from . import config


@dataclass(frozen=True)
class PortfolioKPIs:
    """Top-level portfolio figures, all in the reporting currency (USD)."""

    net_exposure: float
    gross_exposure: float
    total_unrealised_pl: float
    total_var_1d: float
    position_count: int
    # Positions excluded from value-based KPIs because a required input is
    # missing. Surfaced so the UI can warn rather than silently under-report.
    incomplete_position_count: int


def enrich_positions(positions: pd.DataFrame) -> pd.DataFrame:
    """Return a copy with derived columns added.

    Adds ``side``, ``market_value``, ``unrealised_pl`` and
    ``utilisation_pct``. Rows with a missing ``market_price`` propagate NaN
    into the derived value columns rather than being coerced to zero.
    """
    enriched = positions.copy()

    enriched["side"] = np.select(
        [enriched["quantity"] > 0, enriched["quantity"] < 0],
        ["Long", "Short"],
        default="Flat",
    )

    enriched["market_value"] = enriched["quantity"] * enriched["market_price"]
    enriched["unrealised_pl"] = enriched["quantity"] * (
        enriched["market_price"] - enriched["avg_price"]
    )

    # Utilisation against the position's exposure limit. Guard against a zero
    # or missing limit producing infinity.
    limit = enriched["exposure_limit"].replace(0, np.nan)
    enriched["utilisation_pct"] = enriched["market_value"].abs() / limit * 100.0

    return enriched


def has_missing_required_values(positions: pd.DataFrame) -> pd.Series:
    """Boolean Series flagging rows missing any required input value."""
    required = list(config.REQUIRED_VALUE_COLUMNS)
    return positions[required].isna().any(axis=1)


def portfolio_kpis(enriched: pd.DataFrame) -> PortfolioKPIs:
    """Aggregate the enriched positions into top-level KPIs.

    Sums skip missing values (NaN) -- a missing input is excluded from the
    total, never read as zero. ``total_var_1d`` is a simple sum of supplied
    per-position VaR; it ignores diversification and is a prototype figure
    only, not an authoritative portfolio VaR.
    """
    return PortfolioKPIs(
        net_exposure=float(enriched["market_value"].sum(skipna=True)),
        gross_exposure=float(enriched["market_value"].abs().sum(skipna=True)),
        total_unrealised_pl=float(enriched["unrealised_pl"].sum(skipna=True)),
        total_var_1d=float(enriched["var_1d"].sum(skipna=True)),
        position_count=int(len(enriched)),
        incomplete_position_count=int(has_missing_required_values(enriched).sum()),
    )


def aggregate_exposure(enriched: pd.DataFrame, by: str) -> pd.DataFrame:
    """Gross exposure (absolute market value) grouped by a dimension.

    Returned sorted descending so the largest concentration is first.
    """
    grouped = (
        enriched.assign(gross_exposure=enriched["market_value"].abs())
        .groupby(by, dropna=False)["gross_exposure"]
        .sum(min_count=1)
        .reset_index()
        .sort_values("gross_exposure", ascending=False, ignore_index=True)
    )
    return grouped


def aggregate_pl(enriched: pd.DataFrame, by: str) -> pd.DataFrame:
    """Unrealised P/L grouped by a dimension, sorted descending."""
    grouped = (
        enriched.groupby(by, dropna=False)["unrealised_pl"]
        .sum(min_count=1)
        .reset_index()
        .sort_values("unrealised_pl", ascending=False, ignore_index=True)
    )
    return grouped
