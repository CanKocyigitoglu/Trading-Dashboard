"""Pure unit tests for the ingestion run-status decision (no DB, no network)."""

from __future__ import annotations

from app.services.ingestion import _status_for


def test_all_succeeded_is_success():
    assert _status_for(succeeded=9, failed=0) == "success"


def test_none_succeeded_is_failed():
    assert _status_for(succeeded=0, failed=9) == "failed"


def test_some_succeeded_is_partial():
    assert _status_for(succeeded=7, failed=2) == "partial"
