"""Read-only market-data source adapter backed by Yahoo Finance (yfinance).

This is a FREE, UNOFFICIAL source — not the firm's authoritative price feed. The
adapter is read-only and replaceable: a later slice can swap it for an approved
upstream feed without touching the repository, service, schema or API layers.

Source values are preserved exactly, with no conversion. Each instrument carries
the currency and unit of its *native* Yahoo quote — note two real conventions:

* CBOT grains (wheat/corn/soy) quote in **US cents per bushel** -> currency "USc".
* COMEX copper quotes in **USD per pound** -> unit "lb" (not USD/MT).

Prices are read as the bar Close and parsed via ``Decimal(str(...))`` so source
precision survives to the database. The only network call lives in
``fetch_frame``; ``normalise_frame`` is pure so it is tested without network.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal
from typing import cast

import pandas as pd
import yfinance as yf


@dataclass(frozen=True)
class Instrument:
    symbol: str  # canonical app symbol, e.g. "WTI"
    source_symbol: str  # Yahoo ticker (source id), e.g. "CL=F"
    name: str
    commodity: str
    unit: str
    currency: str


@dataclass(frozen=True)
class Observation:
    """One normalised price observation, ready for the repository to persist."""

    symbol: str
    source_symbol: str
    price: Decimal
    currency: str
    unit: str
    source_ts: datetime  # tz-aware, UTC
    data_quality: str  # "ok" for a real source value


# Commodity universe mapped to real Yahoo futures tickers. POWER from the old
# synthetic set is intentionally omitted: there is no reliable free source for it.
INSTRUMENT_UNIVERSE: tuple[Instrument, ...] = (
    Instrument("WTI", "CL=F", "WTI Crude Futures", "WTI Crude", "bbl", "USD"),
    Instrument("BRENT", "BZ=F", "Brent Crude Futures", "Brent Crude", "bbl", "USD"),
    Instrument("NATGAS", "NG=F", "Henry Hub Gas Futures", "Natural Gas", "MMBtu", "USD"),
    Instrument("COPPER", "HG=F", "Copper Futures", "Copper", "lb", "USD"),
    Instrument("ALU", "ALI=F", "Aluminium Futures", "Aluminium", "MT", "USD"),
    Instrument("WHEAT", "ZW=F", "Wheat Futures", "Wheat", "bu", "USc"),
    Instrument("CORN", "ZC=F", "Corn Futures", "Corn", "bu", "USc"),
    Instrument("GOLD", "GC=F", "Gold Futures", "Gold", "oz", "USD"),
    Instrument("SOY", "ZS=F", "Soybean Futures", "Soybean", "bu", "USc"),
)

BY_SYMBOL: dict[str, Instrument] = {i.symbol: i for i in INSTRUMENT_UNIVERSE}

DEFAULT_PERIOD = "1d"
DEFAULT_INTERVAL = "1m"


def fetch_frame(
    source_symbol: str, period: str = DEFAULT_PERIOD, interval: str = DEFAULT_INTERVAL
) -> pd.DataFrame:
    """Network boundary: fetch raw OHLC bars for one Yahoo ticker.

    Isolated in its own function so :func:`normalise_frame` (and everything above
    it) can be tested without public network access, per the backend test rules.
    """
    frame = yf.Ticker(source_symbol).history(period=period, interval=interval, auto_adjust=False)
    return cast(pd.DataFrame, frame)


def normalise_frame(instrument: Instrument, frame: pd.DataFrame) -> list[Observation]:
    """Turn a Yahoo OHLC frame into ordered :class:`Observation`s (oldest first).

    Reads the bar Close, skips rows with no Close (unavailable, never coerced to
    zero), and normalises each bar timestamp to tz-aware UTC.
    """
    if frame is None or frame.empty or "Close" not in frame.columns:
        return []

    observations: list[Observation] = []
    for ts, close in frame["Close"].items():
        if pd.isna(close):
            continue  # unavailable bar, kept distinct from zero
        source_ts = pd.Timestamp(cast(datetime, ts)).to_pydatetime()
        source_ts = (
            source_ts.replace(tzinfo=UTC) if source_ts.tzinfo is None else source_ts.astimezone(UTC)
        )
        observations.append(
            Observation(
                symbol=instrument.symbol,
                source_symbol=instrument.source_symbol,
                price=Decimal(str(close)),  # preserve source precision
                currency=instrument.currency,
                unit=instrument.unit,
                source_ts=source_ts,
                data_quality="ok",
            )
        )
    return observations
