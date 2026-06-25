"""API endpoint tests against the deterministic sample data."""

from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health():
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_summary_matches_sample_data():
    response = client.get("/api/v1/summary")
    assert response.status_code == 200
    body = response.json()
    assert body["currency"] == "USD"
    assert body["position_count"] == 14
    assert body["incomplete_position_count"] == 1
    assert body["net_exposure"] == 8_226_500.0
    assert body["gross_exposure"] == 26_880_500.0
    assert body["total_var_1d_illustrative"] == 1_387_000.0
    assert body["source_timestamp"].startswith("2026-06-24T15:30:00")


def test_positions_list_and_filter():
    full = client.get("/api/v1/positions").json()
    assert full["total"] == 14
    assert full["currency"] == "USD"

    filtered = client.get("/api/v1/positions", params={"desk": "Crude Oil"}).json()
    assert filtered["total"] == 3
    assert {item["desk"] for item in filtered["items"]} == {"Crude Oil"}


def test_positions_pagination():
    page = client.get("/api/v1/positions", params={"limit": 5, "offset": 0}).json()
    assert page["total"] == 14
    assert len(page["items"]) == 5


def test_incomplete_position_reports_nulls_not_zero():
    items = client.get("/api/v1/positions").json()["items"]
    soybean = next(i for i in items if i["position_id"] == "P014")
    assert soybean["market_price"] is None
    assert soybean["market_value"] is None
    assert soybean["data_quality"] == "incomplete"


def test_alerts_include_missing_data_alert():
    body = client.get("/api/v1/alerts").json()
    rule_ids = {a["rule_id"] for a in body["items"]}
    assert "DATA_MISSING_REQUIRED" in rule_ids
    missing = next(a for a in body["items"] if a["rule_id"] == "DATA_MISSING_REQUIRED")
    assert missing["detail_reference"] == "P014"
    assert missing["reason"]


def test_empty_filter_selection_returns_handled_error():
    # Crude Oil desk has no Wheat positions -> zero rows.
    response = client.get("/api/v1/summary", params={"desk": "Crude Oil", "commodity": "Wheat"})
    assert response.status_code == 422
    assert response.json()["code"] == "no_positions_for_filter"

    # Positions and alerts tolerate the same empty selection without erroring.
    positions = client.get("/api/v1/positions", params={"desk": "Crude Oil", "commodity": "Wheat"})
    assert positions.status_code == 200
    assert positions.json()["total"] == 0


def test_filter_options():
    body = client.get("/api/v1/filters").json()
    assert "Crude Oil" in body["desks"]
    assert "Alice Chen" in body["traders"]
    assert "WTI Crude" in body["commodities"]
