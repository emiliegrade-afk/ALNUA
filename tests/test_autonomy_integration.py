"""Autonomie profonde — post hook + CEO approve-step API."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from tests.conftest import HUB_HEADERS


@pytest.fixture
def workflow_runs_dir(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    runs = tmp_path / "workflow_runs"
    runs.mkdir()
    monkeypatch.setattr("services.workflow_engine._RUNS_DIR", runs)
    return runs


@pytest.fixture
def trust_store(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    path = tmp_path / "agent_trust.json"
    monkeypatch.setattr("services.agent_trust._STORE", path)
    return path


def test_trigger_on_pending_approval(workflow_runs_dir: Path, trust_store: Path) -> None:
    from services.content_validation_trigger import trigger_on_post_status

    post = {
        "id": "post-1",
        "status": "pending_approval",
        "text_content": "Launch " + "A" * 80,
        "platform": "linkedin",
        "author_agent_id": "content",
        "project_id": "proj-1",
    }
    with patch("services.event_bus.emit"):
        result = trigger_on_post_status(post, previous_status="draft")
    assert result is not None
    assert result.get("run_id")
    assert result.get("recipe_id") == "content_validation" or result.get("success") is not None


def test_trigger_skips_same_status(workflow_runs_dir: Path) -> None:
    from services.content_validation_trigger import trigger_on_post_status

    post = {"id": "p2", "status": "approved", "text_content": "x" * 50}
    assert trigger_on_post_status(post, previous_status="approved") is None


def test_list_runs_waiting_a_verifier(workflow_runs_dir: Path, trust_store: Path) -> None:
    from services.workflow_engine import list_runs, run_workflow

    with patch("services.event_bus.emit"):
        run_workflow(
            "content_validation",
            {
                "autonomy_level": 0,
                "producer_agent_id": "content",
                "artifact": {
                    "title": "Post",
                    "body": "B" * 100,
                    "status": "ready",
                    "platform": "x",
                },
            },
        )
    waiting = list_runs(limit=10, waiting_a_verifier=True)
    assert len(waiting) >= 1
    assert waiting[0].get("steps_a_verifier")


def test_approve_step_continues_run(workflow_runs_dir: Path, trust_store: Path) -> None:
    from services.workflow_engine import approve_workflow_step, get_run, run_workflow

    with patch("services.event_bus.emit") as emit_mock:
        started = run_workflow(
            "content_validation",
            {
                "autonomy_level": 0,
                "producer_agent_id": "content",
                "project_id": "proj-x",
                "artifact": {
                    "title": "Ship note",
                    "body": "C" * 100,
                    "status": "ready",
                    "platform": "linkedin",
                    "project_id": "proj-x",
                },
            },
        )
    run_id = started["run_id"]
    gate = next(s for s in started["steps"] if s["step_id"] == "quality_gate")
    assert gate["status"] == "A_VERIFIER"

    with patch("services.event_bus.emit") as emit_mock:
        result = approve_workflow_step(run_id, "quality_gate", approver_agent_id="ceo")
    assert result.get("ok") is True
    run = get_run(run_id)
    assert run is not None
    gate_after = next(s for s in run.steps if s.step_id == "quality_gate")
    assert gate_after.status == "OK"
    emit_types = [c.args[0] for c in emit_mock.call_args_list if c.args]
    assert "content_validated" in emit_types or any(
        s.status == "OK" for s in run.steps if s.step_id == "emit_validated"
    )


def test_posts_patch_triggers_validation(
    workflow_runs_dir: Path,
    trust_store: Path,
    hub_client: TestClient,
) -> None:
    updated = {
        "id": "post-99",
        "status": "pending_approval",
        "text_content": "Hello " + "Z" * 80,
        "author_agent_id": "content",
        "platform": "linkedin",
    }
    mock_db = MagicMock()
    mock_db.select.return_value = [
        {"id": "post-99", "status": "draft", "text_content": updated["text_content"]}
    ]
    mock_agent = MagicMock()
    mock_agent.update_post.return_value = updated

    with patch("api.routers.posts.get_supabase", return_value=mock_db):
        with patch("api.routers.posts.ContentAgent", return_value=mock_agent):
            with patch("services.event_bus.emit"):
                resp = hub_client.patch(
                    "/posts/post-99",
                    json={"status": "pending_approval"},
                    headers=HUB_HEADERS,
                )

    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body.get("validation_run_id")
