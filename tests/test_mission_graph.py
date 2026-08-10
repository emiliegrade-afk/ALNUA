"""Mission Graph — Phase B (DEC-023)."""

from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from services.mission_graph_build import mission_from_plan, mission_from_steps
from services.mission_graph_run import refresh_ready_and_blocked, run_mission
from services.mission_graph_store import get_mission, list_missions
from services.plan_executor_models import ExecutionPlan, ExecutionStep, StepResult


@pytest.fixture(autouse=True)
def _missions_tmp(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    root = tmp_path / "missions"
    root.mkdir()
    monkeypatch.setattr(
        "services.mission_graph_store._missions_dir",
        lambda: root,
    )
    monkeypatch.setenv("HUB_API_KEY", "test-hub-key-for-ci")
    monkeypatch.setenv("ISOLATION_ENABLED", "0")
    try:
        from config.settings import get_settings

        get_settings.cache_clear()
    except Exception:
        pass
    yield
    try:
        from config.settings import get_settings

        get_settings.cache_clear()
    except Exception:
        pass


def _fake_step(step: ExecutionStep, max_retries: int = 2) -> StepResult:
    if step.method == "fail":
        return StepResult(
            step_id=step.step_id,
            agent_id=step.agent_id,
            description=step.description,
            success=False,
            result=None,
            error="forced fail",
            duration_ms=1,
            retries=0,
        )
    return StepResult(
        step_id=step.step_id,
        agent_id=step.agent_id,
        description=step.description,
        success=True,
        result={"ok": True, "step": step.step_id},
        error=None,
        duration_ms=1,
        retries=0,
    )


def test_mission_from_steps_parallel_ready() -> None:
    m = mission_from_steps(
        title="API + UI",
        tasks=[
            {
                "task_id": "1",
                "description": "API",
                "agent_id": "dev_backend",
                "method": "noop",
                "depends_on": [],
            },
            {
                "task_id": "2",
                "description": "UI",
                "agent_id": "dev_frontend",
                "method": "noop",
                "depends_on": [],
            },
        ],
    )
    assert m.status == "DRAFTED"
    assert len(m.tasks) == 2
    refresh_ready_and_blocked(m)
    assert {t.status for t in m.tasks} == {"READY"}
    assert m.graph_summary()["edges"] == []


def test_mission_depends_on_sequential(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "services.plan_executor_run._execute_step",
        _fake_step,
    )
    m = mission_from_steps(
        title="Seq",
        tasks=[
            {
                "task_id": "a",
                "description": "Backend",
                "agent_id": "dev_backend",
                "method": "ok",
                "depends_on": [],
            },
            {
                "task_id": "b",
                "description": "Frontend",
                "agent_id": "dev_frontend",
                "method": "ok",
                "depends_on": ["a"],
            },
        ],
    )
    result = run_mission(m.mission_id, max_concurrent=4)
    assert result["status"] == "COMPLETED"
    fresh = get_mission(m.mission_id)
    assert fresh is not None
    assert fresh.task_map()["a"].status == "COMPLETED"
    assert fresh.task_map()["b"].status == "COMPLETED"
    assert fresh.progress_pct() == 100


def test_mission_failure_blocks_dependent(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "services.plan_executor_run._execute_step",
        _fake_step,
    )
    m = mission_from_steps(
        title="Fail cascade",
        tasks=[
            {
                "task_id": "a",
                "description": "Boom",
                "agent_id": "dev_backend",
                "method": "fail",
                "depends_on": [],
            },
            {
                "task_id": "b",
                "description": "After",
                "agent_id": "dev_frontend",
                "method": "ok",
                "depends_on": ["a"],
            },
        ],
    )
    result = run_mission(m.mission_id)
    assert result["status"] in {"FAILED", "BLOCKED"}
    fresh = get_mission(m.mission_id)
    assert fresh is not None
    assert fresh.task_map()["a"].status == "FAILED"
    assert fresh.task_map()["b"].status == "BLOCKED"


def test_mission_from_plan_and_list() -> None:
    plan = ExecutionPlan(
        title="Plan X",
        objective="Build X",
        steps=[
            ExecutionStep(
                step_id="1",
                description="Do",
                agent_id="qa",
                method="ok",
            )
        ],
    )
    m = mission_from_plan(plan, source="from_plan")
    listed = list_missions(limit=10)
    assert any(x["mission_id"] == m.mission_id for x in listed)
    loaded = get_mission(m.mission_id)
    assert loaded is not None
    assert loaded.title == "Plan X"


def test_parallel_batch_runs_both(monkeypatch: pytest.MonkeyPatch) -> None:
    seen: list[str] = []

    def _track(step: ExecutionStep, max_retries: int = 2) -> StepResult:
        seen.append(step.step_id)
        return _fake_step(step, max_retries)

    monkeypatch.setattr("services.plan_executor_run._execute_step", _track)
    m = mission_from_steps(
        title="Parallel",
        tasks=[
            {
                "task_id": "p1",
                "description": "A",
                "agent_id": "dev_backend",
                "method": "ok",
            },
            {
                "task_id": "p2",
                "description": "B",
                "agent_id": "dev_frontend",
                "method": "ok",
            },
        ],
    )
    run_mission(m.mission_id, max_concurrent=2)
    assert set(seen) == {"p1", "p2"}


def test_missions_api_create_and_get(
    hub_client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from tests.conftest import HUB_HEADERS

    monkeypatch.setattr("services.plan_executor_run._execute_step", _fake_step)

    r = hub_client.post(
        "/missions/from-plan",
        headers=HUB_HEADERS,
        json={
            "title": "API test",
            "steps": [
                {
                    "task_id": "1",
                    "description": "x",
                    "agent_id": "qa",
                    "method": "ok",
                }
            ],
            "run": True,
        },
    )
    assert r.status_code == 200, r.text
    body = r.json()
    mid = body["mission"]["mission_id"]
    g = hub_client.get(f"/missions/{mid}", headers=HUB_HEADERS)
    assert g.status_code == 200
    assert g.json()["status"] == "COMPLETED"
    lst = hub_client.get("/missions", headers=HUB_HEADERS)
    assert lst.status_code == 200
    assert any(m["mission_id"] == mid for m in lst.json()["missions"])
