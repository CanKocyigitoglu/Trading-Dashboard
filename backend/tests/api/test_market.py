"""API tests for the /market endpoint in offline synthetic mode.

Synthetic mode needs no database or network, so it exercises the route shape and
labelling deterministically. The DB-backed yahoo path is covered by the
Postgres integration tests (tests/integration).
"""

from __future__ import annotations

import pytest

from app.adapters import market_data_source as mkt
from app.config import Settings, get_settings
from app.main import app


@pytest.fixture
def synthetic_client():
    from fastapi.testclient import TestClient

    app.dependency_overrides[get_settings] = lambda: Settings(market_source="synthetic")
    try:
        yield TestClient(app)
    finally:
        app.dependency_overrides.pop(get_settings, None)


def test_market_overview_shape_and_labels(synthetic_client):
    response = synthetic_client.get("/api/v1/market")
    assert response.status_code == 200
    body = response.json()

    assert body["synthetic"] is True
    assert body["source"] == "synthetic"
    assert "stale_after_seconds" in body
    assert body["as_of"].endswith("Z") or "+00:00" in body["as_of"]

    symbols = {q["symbol"] for q in body["quotes"]}
    assert symbols == {c.symbol for c in mkt.COMMODITY_UNIVERSE}


def test_market_quote_fields_are_consistent(synthetic_client):
    body = synthetic_client.get("/api/v1/market").json()
    quote = body["quotes"][0]

    assert len(quote["series"]) == mkt.WINDOW
    assert quote["currency"] == "USD"
    assert quote["unit"]
    assert quote["stale"] is False
    assert quote["source_ts"] is not None
    assert quote["last_price"] == quote["series"][-1]["price"]
    assert quote["previous_price"] == quote["series"][-2]["price"]
    assert quote["change"] == round(quote["last_price"] - quote["previous_price"], 4)
