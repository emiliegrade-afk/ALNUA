"""Smoke tests for Tier 3 advanced_services endpoints."""

from __future__ import annotations

from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

HUB_HEADERS = {"X-Hub-Key": "test-hub-key-for-ci"}


@pytest.fixture()
def client(hub_client: TestClient) -> TestClient:
    return hub_client


def test_costs_report_endpoint(client: TestClient) -> None:
    res = client.get("/services/costs/report?days=7", headers=HUB_HEADERS)
    assert res.status_code == 200
    body = res.json()
    assert "total_cost_usd" in body
    assert "by_agent" in body


def test_costs_alert_endpoint(client: TestClient) -> None:
    res = client.get("/services/costs/alert?daily_budget_usd=5", headers=HUB_HEADERS)
    assert res.status_code == 200
    assert "severity" in res.json()


def test_events_recent_and_stats(client: TestClient) -> None:
    with patch("services.event_bus._persist_event"):
        client.post(
            "/services/events/emit",
            headers=HUB_HEADERS,
            json={"event_type": "task_completed", "payload": {}, "source_agent": "qa"},
        )

    recent = client.get("/services/events/recent?limit=5", headers=HUB_HEADERS)
    assert recent.status_code == 200
    assert isinstance(recent.json(), list)

    stats = client.get("/services/events/stats", headers=HUB_HEADERS)
    assert stats.status_code == 200
    assert "by_type" in stats.json()


def test_events_types_catalog(client: TestClient) -> None:
    res = client.get("/services/events/types", headers=HUB_HEADERS)
    assert res.status_code == 200
    assert "task_completed" in res.json()


@patch("services.a_b_tester._run_variant")
@patch("services.a_b_tester._judge_results")
def test_ab_test_quick_compare_endpoint(
    mock_judge,
    mock_run,
    client: TestClient,
) -> None:
    from services.a_b_tester import RunResult

    mock_run.side_effect = lambda vd, label, runs: [
        RunResult(
            variant=label,
            agent_id="qa",
            method="handle_instruction",
            result={"ok": label},
            cost_ms=1,
            success=True,
        )
    ]
    mock_judge.return_value = {
        "winner": "B",
        "confidence": 0.8,
        "reasoning": "B wins",
    }

    res = client.post(
        "/services/ab-test/quick-compare",
        headers=HUB_HEADERS,
        json={
            "agent_id": "qa",
            "method": "handle_instruction",
            "kwargs_a": {"instruction": "a"},
            "kwargs_b": {"instruction": "b"},
        },
    )
    assert res.status_code == 200
    assert res.json()["winner"] == "B"


@patch("services.daily_briefing._coo_synthesize")
@patch("services.daily_briefing._collect_leaderboard", return_value={})
@patch("services.daily_briefing._collect_costs", return_value={})
@patch("services.daily_briefing._collect_events", return_value={})
@patch("services.daily_briefing._collect_memory_health", return_value={})
@patch("services.daily_briefing._collect_trends", return_value={})
def test_briefing_daily_endpoint(
    _trends,
    _mem,
    _events,
    _costs,
    _board,
    mock_coo,
    client: TestClient,
) -> None:
    mock_coo.return_value = {
        "headline": "API test",
        "priority_1": "p1",
        "alerts": [],
        "opportunities": [],
    }

    res = client.post(
        "/services/briefing/daily",
        headers=HUB_HEADERS,
        json={"context": "ci", "include_trends": True},
    )
    assert res.status_code == 200
    assert res.json()["coo_brief"]["headline"] == "API test"
