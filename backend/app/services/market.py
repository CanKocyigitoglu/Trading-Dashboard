"""Use-case orchestration for the Live Market page.

A thin entry point over the synthetic market-data adapter that owns the default
evaluation time. ``now`` is injectable so the snapshot is reproducible in tests,
mirroring ``dashboard.get_summary``. A distinct use case from the dashboard, so
it lives in its own module.
"""

from __future__ import annotations

from datetime import UTC, datetime

from ..adapters import market_data_source
from ..schemas.models import MarketOverviewResponse


def get_market_overview(now: datetime | None = None) -> MarketOverviewResponse:
    now = now or datetime.now(UTC)
    return market_data_source.build_overview(now)
