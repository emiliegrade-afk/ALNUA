"""Phase 4 — API route consolidation tests."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

HUB_HEADERS = {"X-Hub-Key": "test-hub-key-for-ci"}


@pytest.fixture()
def client(monkeypatch: pytest.MonkeyPatch) -> TestClient:
    monkeypatch.setenv("HUB_API_KEY", "test-hub-key-for-ci")
    from config.settings import get_settings

    get_settings.cache_clear()
    monkeypatch.setattr("database.supabase_client.get_supabase", lambda: MagicMock())
    from api.app import app

    return TestClient(app)


def test_finance_summary_on_finances_router(client: TestClient) -> None:
    with patch(
        "api.routers.finances.get_or_generate_summary",
        return_value={"month": "2026-06", "total_expense": 0},
    ):
        res = client.get("/finances/summary/2026-06", headers=HUB_HEADERS)
    assert res.status_code == 200
    assert res.json()["month"] == "2026-06"


def test_briefing_today_uses_facade(client: TestClient) -> None:
    with patch(
        "api.routers.briefing.fetch_operational_briefing_for_date",
        return_value={"id": "b1", "date": "2026-06-15"},
    ):
        res = client.get("/briefing/today", headers=HUB_HEADERS)
    assert res.status_code == 200
    assert res.json()["id"] == "b1"


def test_gdd_router_absent_when_flag_off(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    from config.settings import get_settings

    monkeypatch.setenv("GDD_MANAGER_ENABLED", "0")
    get_settings.cache_clear()

    res = client.get("/gdd/proj-1/sections", headers=HUB_HEADERS)
    assert res.status_code == 404
