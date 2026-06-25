"""API tests for the synthetic /market endpoint."""

from __future__ import annotations

from fastapi.testclient import TestClient

from app.adapters import market_data_source as mkt
from app.main import app

client = TestClient(app)


def test_market_overview_shape_and_synthetic_label():
    response = client.get("/api/v1/market")
    assert response.status_code == 200
    body = response.json()

    assert body["synthetic"] is True
    assert body["as_of"].endswith("Z") or "+00:00" in body["as_of"]

    symbols = {q["symbol"] for q in body["quotes"]}
    assert symbols == {c.symbol for c in mkt.COMMODITY_UNIVERSE}


def test_market_quote_fields_are_consistent():
    body = client.get("/api/v1/market").json()
    quote = body["quotes"][0]

    assert len(quote["series"]) == mkt.WINDOW
    assert quote["currency"] == "USD"
    assert quote["unit"]
    assert quote["last_price"] == quote["series"][-1]["price"]
    assert quote["previous_price"] == quote["series"][-2]["price"]
    assert quote["change"] == round(quote["last_price"] - quote["previous_price"], 4)
