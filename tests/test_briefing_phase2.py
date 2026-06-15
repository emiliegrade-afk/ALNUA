"""Phase 2 tests — briefing unification (COO tab + unified generate)."""

from __future__ import annotations

import os
from typing import Any
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

os.environ.setdefault("SUPABASE_URL", "https://example.supabase.co")
os.environ.setdefault("SUPABASE_KEY", "test-supabase-key")
os.environ.setdefault("OPENROUTER_API_KEY", "test-openrouter-key")
os.environ.setdefault("HUB_API_KEY", "test-hub-key-for-ci")
os.environ.setdefault("ENVIRONMENT", "development")

HUB_HEADERS = {"X-Hub-Key": "test-hub-key-for-ci"}


class _FakeDB:
    def select(self, *args: Any, **kwargs: Any) -> list[dict[str, Any]]:
        return []

    def insert(self, *args: Any, **kwargs: Any) -> dict[str, Any]:
        return {"id": "brief-1"}

    def update(self, *args: Any, **kwargs: Any) -> dict[str, Any]:
        return {"id": "brief-1"}

    def table(self, name: str) -> "_FakeDB":
        return self

    def order(self, *args: Any, **kwargs: Any) -> "_FakeDB":
        return self

    def limit(self, *args: Any, **kwargs: Any) -> "_FakeDB":
        return self

    def execute(self) -> MagicMock:
        m = MagicMock()
        m.data = []
        return m


@pytest.fixture()
def client(monkeypatch: pytest.MonkeyPatch) -> TestClient:
    from config.settings import get_settings

    monkeypatch.setenv("HUB_API_KEY", "test-hub-key-for-ci")
    get_settings.cache_clear()
    monkeypatch.setattr("database.supabase_client.get_supabase", lambda: _FakeDB())
    from api.app import app

    return TestClient(app)


def test_admin_flags_includes_briefing_unified(client: TestClient) -> None:
    res = client.get("/admin/flags", headers=HUB_HEADERS)
    assert res.status_code == 200
    data = res.json()
    assert "briefing_unified_generate" in data
    assert "briefing_coo_section_enabled" in data


def test_briefing_generate_operational_only(monkeypatch: pytest.MonkeyPatch) -> None:
    from config.settings import get_settings

    monkeypatch.setenv("BRIEFING_UNIFIED_GENERATE", "0")
    get_settings.cache_clear()

    fake_row = {
        "id": "b1",
        "date": "2026-06-13",
        "summary": "Op brief",
        "raw_data": {},
        "has_urgent": False,
        "urgent_count": 0,
        "pending_count": 0,
    }

    with (
        patch(
            "api.routers.briefing.generate_and_store_daily_briefing",
            return_value=fake_row,
        ) as mock_gen,
        patch("services.orchestration.run_morning_orchestration") as mock_orch,
    ):
        from api.routers.briefing import briefing_generate

        out = briefing_generate()

    assert out == fake_row
    mock_gen.assert_called_once_with(replace_existing=True)
    mock_orch.assert_not_called()


def test_briefing_generate_unified_when_flag_on(monkeypatch: pytest.MonkeyPatch) -> None:
    from config.settings import get_settings

    monkeypatch.setenv("BRIEFING_UNIFIED_GENERATE", "1")
    get_settings.cache_clear()

    fake_row = {
        "id": "b1",
        "date": "2026-06-13",
        "summary": "Op brief",
        "raw_data": {},
        "has_urgent": False,
        "urgent_count": 0,
        "pending_count": 0,
    }
    fake_orch = {
        "workflow": "morning",
        "success": True,
        "briefing_result": {"coo_brief": {"headline": "COO"}},
    }

    with (
        patch(
            "api.routers.briefing.generate_and_store_daily_briefing",
            return_value=fake_row,
        ),
        patch(
            "services.orchestration.run_morning_orchestration",
            return_value=fake_orch,
        ) as mock_orch,
    ):
        from api.routers.briefing import briefing_generate

        out = briefing_generate()

    assert out["unified"] is True
    assert out["orchestration"] == fake_orch
    mock_orch.assert_called_once_with()


def test_briefing_facade_coo_enabled_gate(monkeypatch: pytest.MonkeyPatch) -> None:
    from config.settings import get_settings
    from services.facades.briefing_facade import is_briefing_coo_section_enabled

    monkeypatch.setenv("BRIEFING_COO_SECTION_ENABLED", "0")
    get_settings.cache_clear()
    assert is_briefing_coo_section_enabled() is False

    monkeypatch.setenv("BRIEFING_COO_SECTION_ENABLED", "1")
    get_settings.cache_clear()
    assert is_briefing_coo_section_enabled() is True
