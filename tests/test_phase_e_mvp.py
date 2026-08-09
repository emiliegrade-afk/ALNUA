"""Phase E MVP — validation recipes, trust, review board, cross-dept."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest


@pytest.fixture
def trust_store(tmp_path, monkeypatch):
    path = tmp_path / "agent_trust.json"
    monkeypatch.setattr("services.agent_trust._STORE", path)
    return path


@pytest.fixture
def cross_dept_queue(tmp_path, monkeypatch):
    path = tmp_path / "cross_dept_queue.json"
    monkeypatch.setattr("services.cross_dept_handlers._QUEUE", path)
    return path


@pytest.fixture
def workflow_runs_dir(tmp_path, monkeypatch):
    runs = tmp_path / "workflow_runs"
    runs.mkdir()
    monkeypatch.setattr("services.workflow_engine._RUNS_DIR", runs)
    return runs


def test_list_recipes_includes_validation() -> None:
    from services.workflow_engine import list_recipes

    ids = {r["id"] for r in list_recipes()}
    assert "content_validation" in ids
    assert "campaign_validation" in ids


def test_quality_gate_thresholds() -> None:
    from config.quality_gates import evaluate_gate, threshold_for

    assert threshold_for("brand") == 90.0
    weak = evaluate_gate("content", {"title": "x", "body": "short"})
    assert weak["gate_open"] is False
    strong = evaluate_gate(
        "content",
        {
            "title": "Launch post",
            "body": "A" * 80,
            "status": "ready",
            "project_id": "p1",
            "platform": "linkedin",
        },
    )
    assert strong["gate_open"] is True
    assert strong["score"] >= strong["threshold"]


def test_trust_updates_on_validation(trust_store: Path) -> None:
    from services.agent_trust import get_trust, record_validation

    before = get_trust("content")
    assert before["provisional"] is True
    after = record_validation("content", success=True, note="test")
    assert after["score"] > before["score"]
    assert after["successes"] == 1
    fail = record_validation("content", success=False, weight=2.0, note="fail")
    assert fail["score"] < after["score"]
    assert trust_store.exists()


def test_review_board_records_trust(trust_store: Path) -> None:
    from services.review_board import evaluate_submission

    result = evaluate_submission(
        department="content",
        artifact={
            "title": "Solid brief",
            "body": "B" * 100,
            "status": "ready",
            "campaign_id": "c1",
        },
        producer_agent_id="content",
        record_trust=True,
    )
    assert result["gate_open"] is True
    assert result["recommendation"] == "approve"
    assert result["trust_after"]["samples"] >= 1


def test_content_validation_autonomy3(
    workflow_runs_dir: Path,
    trust_store: Path,
    cross_dept_queue: Path,
) -> None:
    from services.workflow_engine import run_workflow

    with patch("services.event_bus.emit") as emit_mock:
        result = run_workflow(
            "content_validation",
            {
                "autonomy_level": 3,
                "producer_agent_id": "content",
                "project_id": "proj-1",
                "artifact": {
                    "title": "Product update",
                    "body": "C" * 100,
                    "status": "ready",
                    "platform": "x",
                    "project_id": "proj-1",
                },
            },
        )

    assert result["success"] is True
    assert result["status"] == "completed"
    types = [c.args[0] for c in emit_mock.call_args_list if c.args]
    assert "content_validated" in types
    assert "project_validated" in types


def test_content_validation_blocks_weak_artifact(workflow_runs_dir: Path) -> None:
    from services.workflow_engine import run_workflow

    result = run_workflow(
        "content_validation",
        {
            "autonomy_level": 3,
            "artifact": {"title": "Hi", "body": "tiny"},
        },
    )
    assert result["blocked"] is True
    assert result["blocked_at_step"] == "quality_gate"


def test_autonomy0_marks_gate_a_verifier(workflow_runs_dir: Path) -> None:
    from services.workflow_engine import run_workflow

    result = run_workflow(
        "content_validation",
        {
            "autonomy_level": 0,
            "producer_agent_id": "content",
            "artifact": {
                "title": "Product update",
                "body": "D" * 100,
                "status": "ready",
                "platform": "linkedin",
            },
        },
    )
    assert result["success"] is True
    gate = next(s for s in result["steps"] if s["step_id"] == "quality_gate")
    assert gate["status"] == "A_VERIFIER"


def test_cross_dept_fan_out(cross_dept_queue: Path) -> None:
    from services.cross_dept_handlers import list_cross_dept_queue, on_project_validated
    from services.event_bus import Event

    event = Event(
        event_type="project_validated",
        payload={"title": "App v2", "project_id": "p2", "score": 90},
        source_agent="qa",
    )
    on_project_validated(event)
    items = list_cross_dept_queue(limit=10)
    depts = {i["department"] for i in items}
    assert {"marketing", "finances", "analytics"} <= depts
    assert cross_dept_queue.exists()
