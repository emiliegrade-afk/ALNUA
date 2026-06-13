"""Tests for orchestration endpoints and service."""

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
        return {"id": "fake-log-id"}

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


def test_orchestration_workflows_catalog(client: TestClient) -> None:
    res = client.get("/orchestration/workflows", headers=HUB_HEADERS)
    assert res.status_code == 200
    data = res.json()
    assert len(data) >= 5
    ids = {w["id"] for w in data}
    assert "morning" in ids
    assert "spec_qa_chain" in ids


def test_orchestration_requires_hub_key(client: TestClient) -> None:
    res = client.get("/orchestration/workflows")
    assert res.status_code == 401


@patch("services.orchestration.run_morning_orchestration")
def test_orchestration_morning_endpoint(mock_run: MagicMock, client: TestClient) -> None:
    mock_run.return_value = {
        "workflow": "morning",
        "success": True,
        "coo_plan": "Priorité 1: QA Wyrdheim",
    }
    res = client.post(
        "/orchestration/morning",
        headers=HUB_HEADERS,
        json={"weekly_plan": True},
    )
    assert res.status_code == 200
    assert res.json()["success"] is True
    mock_run.assert_called_once_with(weekly_plan=True)


@patch("services.orchestration.run_spec_qa_chain")
def test_orchestration_spec_qa_endpoint(mock_run: MagicMock, client: TestClient) -> None:
    mock_run.return_value = {"workflow": "spec_qa_chain", "success": True, "consensus_spec": "ok"}
    res = client.post(
        "/orchestration/spec-qa-chain",
        headers=HUB_HEADERS,
        json={"spec_text": "L'agent doit valider les scores de compétition chaque jour."},
    )
    assert res.status_code == 200
    assert res.json()["success"] is True


def test_run_morning_orchestration_partial_failure() -> None:
    from services.orchestration import run_morning_orchestration

    with (
        patch(
            "services.daily_briefing.run_daily_briefing",
            side_effect=RuntimeError("briefing down"),
        ),
        patch("services.orchestration._log_run"),
        patch("services.orchestration.get_supabase", return_value=_FakeDB()),
    ):
        result = run_morning_orchestration()

    assert result["success"] is False
    assert result["briefing_error"] is not None
    assert result["coo_plan"] is None


def test_spec_qa_chain_creates_ticket() -> None:
    from services.orchestration import run_spec_qa_chain

    fake_debate = {
        "consensus_spec": "Spec finale validée",
        "final_verdict": "approve",
        "divergences": [],
    }
    fake_ticket = {"id": "t1", "title": "[Spec validée] Test"}

    with (
        patch("services.adversarial_spec.debate_spec", return_value=fake_debate),
        patch("services.orchestration._resolve_project_id", return_value="proj-1"),
        patch("services.orchestration._notify", return_value={"telegram": True, "discord": False}),
        patch("services.orchestration._log_run"),
        patch("agents.qa_agent.QAAgent") as mock_qa,
    ):
        mock_qa.return_value.create_ticket_from_report.return_value = fake_ticket
        result = run_spec_qa_chain("Spec initiale longue pour le test", context="Feature test")

    assert result["success"] is True
    assert result["qa_ticket"] == fake_ticket
    mock_qa.return_value.create_ticket_from_report.assert_called_once()


    from services.orchestration import WORKFLOW_CATALOG

    for wf in WORKFLOW_CATALOG:
        assert "id" in wf
        assert "endpoint" in wf
        assert wf["endpoint"].startswith("POST /orchestration/") or wf["endpoint"].startswith("GET /orchestration/")
