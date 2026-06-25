"""Read-only synthetic market-data source adapter.

Generates illustrative, time-varying commodity prices for the Live Market page.
This is NOT a real market-data feed: every value is synthetic and is clearly
labelled as such in the API and UI. The adapter is read-only and replaceable,
mirroring ``positions_source.py`` — a later slice can swap it for an approved
upstream price source without changing the service, schema or API layers.

Prices are deterministic functions of ``(symbol, time bucket)``: the same bucket
always yields the same price, so output is fully reproducible for tests, while
the sliding window of recent buckets makes each series move on every poll.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from datetime import UTC, datetime

from ..schemas.models import MarketOverviewResponse, MarketQuote, MarketSeriesPoint

BUCKET_SECONDS = 5  # one synthetic tick every 5 seconds
WINDOW = 60  # points kept in the rolling series (~5 minutes of history)


@dataclass(frozen=True)
class Commodity:
    symbol: str
    name: str
    commodity: str
    unit: str
    currency: str
    anchor: float  # illustrative price level, coherent with the sample positions
    vol_pct: float  # bound on the synthetic wiggle, as a fraction of anchor


# Coherent with data/sample/positions.csv (all USD). Anchors approximate the
# sample market levels; vol_pct sets how far the synthetic price wanders.
COMMODITY_UNIVERSE: tuple[Commodity, ...] = (
    Commodity("WTI", "WTI Crude Futures", "WTI Crude", "bbl", "USD", 78.20, 0.03),
    Commodity("BRENT", "Brent Crude Futures", "Brent Crude", "bbl", "USD", 80.90, 0.03),
    Commodity("NATGAS", "Henry Hub Gas Futures", "Natural Gas", "MMBtu", "USD", 2.85, 0.05),
    Commodity("POWER", "German Power Baseload", "Power", "MWh", "USD", 95.50, 0.04),
    Commodity("COPPER", "Copper Futures", "Copper", "MT", "USD", 9650.0, 0.02),
    Commodity("ALU", "Aluminium Futures", "Aluminium", "MT", "USD", 2380.0, 0.02),
    Commodity("WHEAT", "Wheat Futures", "Wheat", "bu", "USD", 5.95, 0.03),
    Commodity("CORN", "Corn Futures", "Corn", "bu", "USD", 4.62, 0.03),
    Commodity("GOLD", "Gold Futures", "Gold", "oz", "USD", 2410.0, 0.015),
    Commodity("SOY", "Soybean Futures", "Soybean", "bu", "USD", 11.20, 0.03),
)


def bucket_index_for(now_utc: datetime) -> int:
    """Index of the 5-second bucket containing ``now_utc``."""
    return int(now_utc.timestamp()) // BUCKET_SECONDS


def _bucket_time(bucket: int) -> datetime:
    """UTC timestamp at the start of ``bucket`` (tz-aware)."""
    return datetime.fromtimestamp(bucket * BUCKET_SECONDS, tz=UTC)


def _wiggle(symbol: str, bucket: int) -> float:
    """Deterministic pseudo-random value in [-1, 1] for ``(symbol, bucket)``.

    Uses sha256 rather than the built-in ``hash()``, whose string hashing is
    salted per process (``PYTHONHASHSEED``) and would not reproduce across runs
    or tests.
    """
    digest = hashlib.sha256(f"{symbol}:{bucket}".encode()).digest()
    unit = int.from_bytes(digest[:8], "big") / 2**64  # [0, 1)
    return unit * 2 - 1


def price_at(symbol: str, anchor: float, vol_pct: float, bucket: int) -> float:
    """Synthetic illustrative price for ``symbol`` at ``bucket``.

    Two harmonics (fast + slow) give a smoother, less jagged line than raw
    per-bucket noise while staying bounded within roughly +/- vol_pct of anchor.
    """
    drift = (_wiggle(symbol, bucket) + 0.5 * _wiggle(symbol, bucket // 4)) / 1.5
    return round(anchor * (1 + vol_pct * drift), 4)


def build_quote(commodity: Commodity, now_utc: datetime) -> MarketQuote:
    """Assemble a rolling-window quote for one commodity ending at ``now_utc``."""
    current = bucket_index_for(now_utc)
    series = [
        MarketSeriesPoint(
            t=_bucket_time(b),
            price=price_at(commodity.symbol, commodity.anchor, commodity.vol_pct, b),
        )
        for b in range(current - WINDOW + 1, current + 1)
    ]
    last = series[-1].price
    previous = series[-2].price
    change = round(last - previous, 4)
    change_pct = None if previous == 0 else round(change / previous * 100, 4)
    as_of = _bucket_time(current)
    return MarketQuote(
        symbol=commodity.symbol,
        name=commodity.name,
        commodity=commodity.commodity,
        unit=commodity.unit,
        currency=commodity.currency,
        last_price=last,
        previous_price=previous,
        change=change,
        change_pct=change_pct,
        as_of=as_of,
        source_ts=as_of,
        ingested_at=now_utc,
        stale=False,
        series=series,
    )


def build_overview(now_utc: datetime, stale_after_seconds: int) -> MarketOverviewResponse:
    """Build the full synthetic market snapshot at ``now_utc``."""
    return MarketOverviewResponse(
        as_of=_bucket_time(bucket_index_for(now_utc)),
        source="synthetic",
        synthetic=True,
        stale_after_seconds=stale_after_seconds,
        quotes=[build_quote(c, now_utc) for c in COMMODITY_UNIVERSE],
    )
