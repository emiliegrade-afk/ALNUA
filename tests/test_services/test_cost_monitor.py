"""Tests for services/cost_monitor.py."""

from __future__ import annotations

import time

import pytest

from services import cost_monitor


@pytest.fixture(autouse=True)
def isolated_cost_log(tmp_path, monkeypatch):
    """Isolate cost log per test — no cross-test pollution."""
    log_path = tmp_path / "cost_log.json"
    monkeypatch.setattr(cost_monitor, "_COST_LOG_PATH", log_path)
    cost_monitor._cost_log = []
    cost_monitor._loaded = True
    yield
    cost_monitor._cost_log = []
    cost_monitor._loaded = False


def test_record_call_computes_cost() -> None:
    cost = cost_monitor.record_call(
        agent_id="qa",
        model="google/gemini-flash-1.5",
        prompt_tokens=1000,
        completion_tokens=500,
        method="review",
    )
    assert cost > 0
    assert len(cost_monitor._cost_log) == 1
    assert cost_monitor._cost_log[0]["agent_id"] == "qa"


def test_get_cost_report_aggregates_by_agent() -> None:
    cost_monitor.record_call("dev_app", "openai/gpt-4o-mini", 100, 50)
    cost_monitor.record_call("dev_app", "openai/gpt-4o-mini", 200, 100)
    cost_monitor.record_call("qa", "anthropic/claude-haiku-4-5", 300, 150)

    report = cost_monitor.get_cost_report(days=7)
    assert report["total_calls"] == 3
    assert report["total_cost_usd"] > 0
    assert "dev_app" in report["by_agent"]
    assert report["by_agent"]["dev_app"]["calls"] == 2


def test_check_budget_alert_severity() -> None:
    cost_monitor.record_call("coo", "default", 500_000, 500_000)

    alert = cost_monitor.check_budget_alert(daily_budget_usd=0.01)
    assert alert["alert"] is True
    assert alert["severity"] in {"warning", "critical"}
    assert alert["spent_usd"] > 0


def test_get_monthly_summary_shape() -> None:
    cost_monitor.record_call("marketing", "default", 100, 100)
    summary = cost_monitor.get_monthly_summary()
    assert "month" in summary
    assert "total_cost_usd" in summary
    assert "by_agent" in summary


def test_get_daily_costs_legacy_shape() -> None:
    cost_monitor.record_call("analyst_data", "default", 50, 50)
    daily = cost_monitor.get_daily_costs()
    assert "date" in daily
    assert "total_usd" in daily
    assert "by_agent" in daily
