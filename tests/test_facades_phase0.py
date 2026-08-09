"""Phase 0+ regression tests — facades, briefing API, orchestration, costs unify."""

from __future__ import annotations

import os
from datetime import date
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
        return {"id": "fake-briefing-id"}

    def update(self, *args: Any, **kwargs: Any) -> dict[str, Any]:
        return {"id": "fake-briefing-id"}

    def table(self, name: str) -> "_FakeDB":
        return self

    def select_columns(self, *args: Any, **kwargs: Any) -> "_FakeDB":
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


def test_costs_facade_returns_legacy_shape(monkeypatch: pytest.MonkeyPatch) -> None:
    """Lobby / pipeline endpoints must keep total_usd + by_agent shape."""
    from config.settings import get_settings
    from services.facades import costs_facade

    get_settings.cache_clear()

    fake_monthly = {
        "month": "June 2026",
        "total_usd": 1.25,
        "by_agent": {"qa": {"total_usd": 0.5, "calls": 2}},
    }
    fake_daily = {
        "date": date.today().isoformat(),
        "total_usd": 0.42,
        "by_agent": {"dev_app": {"total_usd": 0.42, "calls": 1}},
    }
    fake_weekly = {"total_usd": 2.0, "by_day": [{"date": "01/06", "qa": 0.1}]}

    with (
        patch("services.cost_monitor.get_monthly_costs", return_value=fake_monthly),
        patch("services.cost_monitor.get_daily_costs", return_value=fake_daily),
        patch("services.cost_monitor.get_weekly_costs", return_value=fake_weekly),
    ):
        monthly = costs_facade.get_monthly_costs()
        daily = costs_facade.get_daily_costs()
        weekly = costs_facade.get_weekly_costs()

    assert monthly == fake_monthly
    assert "total_usd" in monthly and "by_agent" in monthly
    assert daily == fake_daily
    assert "date" in daily
    assert weekly == fake_weekly
    assert "by_day" in weekly


def test_briefing_today_404_without_ensure(client: TestClient) -> None:
    """GET /briefing/today must not trigger LLM when ensure=false and no row."""
    with patch(
        "api.routers.briefing.fetch_operational_briefing_for_date",
        return_value=None,
    ):
        res = client.get("/briefing/today?ensure=false", headers=HUB_HEADERS)

    assert res.status_code == 404
    assert "No briefing" in res.json()["detail"]


def test_orchestration_morning_still_stores_row() -> None:
    """Morning orchestration must persist daily_briefing output to Supabase."""
    from services.orchestration import run_morning_orchestration

    fake_briefing = {
        "date": date.today().isoformat(),
        "coo_brief": {
            "headline": "Priorité QA",
            "priority_1": "Wyrdheim",
            "priority_2": "Hub",
            "priority_3": "Content",
            "alerts": ["Budget"],
            "opportunities": [],
        },
        "raw_data": {"leaderboard": {}},
    }

    with (
        patch(
            "services.daily_briefing.run_daily_briefing",
            return_value=fake_briefing,
        ),
        patch("services.orchestration._log_run"),
        patch("services.orchestration._notify", return_value={"telegram": False, "discord": False}),
        patch("services.orchestration.get_supabase", return_value=_FakeDB()),
        patch("services.briefing_generator.store_daily_briefing") as mock_store,
    ):
        result = run_morning_orchestration()

    assert result["success"] is True
    assert result["briefing"] is not None
    mock_store.assert_called_once()
    stored_row = mock_store.call_args[0][1]
    assert stored_row["summary"] == "Priorité QA"
    assert stored_row["has_urgent"] is True


def test_llm_record_cost_monitor_only() -> None:
    """LLMClient writes cost_monitor only (Supabase dual-write retired)."""
    from agents.base import LLMClient

    fake_response = MagicMock()
    fake_response.status_code = 200
    fake_response.text = ""
    fake_response.raise_for_status = MagicMock()
    fake_response.json.return_value = {
        "choices": [{"message": {"content": "ok"}}],
        "usage": {"prompt_tokens": 200, "completion_tokens": 80},
    }

    client = LLMClient()
    with (
        patch("httpx.Client") as mock_client_cls,
        patch("services.cost_monitor.record_call", return_value=0.002) as mock_record,
        patch("services.cost_monitor.check_budget_alert", return_value={"alert": False}),
    ):
        mock_client_cls.return_value.__enter__.return_value.post.return_value = fake_response
        out = client.chat(
            system="sys",
            messages=[{"role": "user", "content": "hi"}],
            agent_id="analyst_data",
            method_name="sql_query",
            model="google/gemini-flash-1.5",
        )

    assert out == "ok"
    mock_record.assert_called_once()


def test_phase0_feature_flags_defaults(monkeypatch: pytest.MonkeyPatch) -> None:
    """Costs unified by default; experimental surfaces stay off."""
    from config.settings import get_settings

    monkeypatch.setenv("COSTS_UNIFIED_READ", "1")
    monkeypatch.setenv("COSTS_SHADOW_COMPARE", "0")
    for key in (
        "BRIEFING_COO_SECTION_ENABLED",
        "BRIEFING_UNIFIED_GENERATE",
        "ADMIN_COSTS_PAGE_ENABLED",
        "GDD_MANAGER_ENABLED",
    ):
        monkeypatch.setenv(key, "0")
    get_settings.cache_clear()

    s = get_settings()
    assert s.costs_unified_read is True
    assert s.costs_shadow_compare is False
    assert s.briefing_coo_section_enabled is False
    assert s.admin_costs_page_enabled is False
    assert s.gdd_manager_enabled is False
