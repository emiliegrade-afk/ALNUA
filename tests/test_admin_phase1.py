"""Phase 1 tests — admin flags API, Telegram costs facade."""

from __future__ import annotations

import os
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

os.environ.setdefault("SUPABASE_URL", "https://example.supabase.co")
os.environ.setdefault("SUPABASE_KEY", "test-supabase-key")
os.environ.setdefault("OPENROUTER_API_KEY", "test-openrouter-key")
os.environ.setdefault("HUB_API_KEY", "test-hub-key-for-ci")
os.environ.setdefault("ENVIRONMENT", "development")

HUB_HEADERS = {"X-Hub-Key": "test-hub-key-for-ci"}


@pytest.fixture()
def client(monkeypatch: pytest.MonkeyPatch) -> TestClient:
    from config.settings import get_settings

    monkeypatch.setenv("HUB_API_KEY", "test-hub-key-for-ci")
    monkeypatch.setenv("ENVIRONMENT", "development")
    get_settings.cache_clear()
    monkeypatch.setattr("database.supabase_client.get_supabase", lambda: MagicMock())
    from api.app import app

    return TestClient(app)


def test_admin_flags_endpoint(client: TestClient) -> None:
    res = client.get("/admin/flags", headers=HUB_HEADERS)
    assert res.status_code == 200
    data = res.json()
    assert "admin_costs_page_enabled" in data
    assert "admin_events_page_enabled" in data
    assert "admin_ab_test_page_enabled" in data
    assert data["preview_allowed"] is True
    assert data["environment"] == "development"


def test_admin_flags_requires_hub_key(client: TestClient) -> None:
    res = client.get("/admin/flags")
    assert res.status_code == 401


def test_telegram_costs_report_unified(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from config.settings import get_settings
    from services.facades import costs_facade

    get_settings.cache_clear()

    fake = {"date": "2026-06-13", "total_usd": 1.5, "by_agent": {"qa": {"total_usd": 1.5, "calls": 2}}}

    with patch("services.facades.costs_facade.get_daily_costs", return_value=fake):
        out = costs_facade.get_telegram_costs_report("day")

    assert "1.5" in out
    assert "qa" in out


def test_costs_report_endpoint_smoke(client: TestClient) -> None:
    res = client.get("/services/costs/report?days=7", headers=HUB_HEADERS)
    assert res.status_code == 200
    body = res.json()
    assert "total_cost_usd" in body
    assert "by_agent" in body


def test_events_recent_endpoint_smoke(client: TestClient) -> None:
    res = client.get("/services/events/recent?limit=5", headers=HUB_HEADERS)
    assert res.status_code == 200
    assert isinstance(res.json(), list)
