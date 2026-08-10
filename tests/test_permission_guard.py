"""PermissionGuard + Trust Graph — Phase E (DEC-026)."""

from __future__ import annotations

import pytest

from services.merge_policy import MergeDeniedError, assert_can_merge, can_merge
from services.permission_guard import (
    PermissionDeniedError,
    check_capability,
    require_capability,
)


@pytest.fixture
def trust_graph_path(tmp_path, monkeypatch: pytest.MonkeyPatch):
    path = tmp_path / "trust_graph.jsonl"
    monkeypatch.setattr("services.trust_graph._STORE", path)
    monkeypatch.setenv("PERMISSION_GUARD_ENABLED", "1")
    try:
        from config.settings import get_settings

        get_settings.cache_clear()
    except Exception:
        pass
    return path


def test_dev_app_denied_merge_main(trust_graph_path) -> None:
    decision = check_capability("dev_app", "git:merge:main", resource="branch:main")
    assert decision["allowed"] is False
    assert decision["reason"] == "pack_deny"
    with pytest.raises(PermissionDeniedError):
        require_capability("dev_app", "git:merge:main")
    text = trust_graph_path.read_text(encoding="utf-8")
    assert "git:merge:main" in text
    assert "pack_deny" in text


def test_integrator_allowed_staging(trust_graph_path) -> None:
    decision = check_capability("dev_integrator", "git:merge:staging")
    assert decision["allowed"] is True
    assert_can_merge("dev_integrator", "staging")


def test_dev_app_assert_merge_main_no_side_effect(trust_graph_path) -> None:
    # Policy may already deny; capability must also deny without merge side-effect
    ok, _ = can_merge("dev_app", "main")
    assert ok is False
    with pytest.raises(MergeDeniedError):
        assert_can_merge("dev_app", "main")
    # Even if policy were open, capability blocks — simulate via require
    with pytest.raises(PermissionDeniedError):
        require_capability("dev_app", "git:merge:main", resource="branch:main")


def test_unknown_capability_denied(trust_graph_path) -> None:
    d = check_capability("coo", "nuclear:launch")
    assert d["allowed"] is False
    assert d["reason"] == "unknown_capability"


def test_guard_disabled_allows(trust_graph_path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("PERMISSION_GUARD_ENABLED", "0")
    try:
        from config.settings import get_settings

        get_settings.cache_clear()
    except Exception:
        pass
    d = check_capability("dev_app", "git:merge:main")
    assert d["allowed"] is True
    assert d["reason"] == "guard_disabled"


def test_ads_spend_pack(trust_graph_path) -> None:
    assert check_capability("ads", "ads:spend")["allowed"] is True
    assert check_capability("dev_app", "ads:spend")["allowed"] is False


def test_mail_send_pack(trust_graph_path) -> None:
    assert check_capability("secretary", "mail:send")["allowed"] is True
    assert check_capability("coo", "mail:send")["allowed"] is True
    assert check_capability("system", "mail:send")["allowed"] is True
    assert check_capability("dev_app", "mail:send")["allowed"] is False


def test_github_pr_caps(trust_graph_path) -> None:
    assert check_capability("dev_frontend", "github:pr:create")["allowed"] is True
    assert check_capability("dev_frontend", "github:pr:merge")["allowed"] is False
    assert check_capability("dev_integrator", "github:pr:merge")["allowed"] is True
    assert check_capability("coding_pipeline", "github:pr:merge")["allowed"] is True


def test_workflow_abort_mission(trust_graph_path, tmp_path, monkeypatch: pytest.MonkeyPatch) -> None:
    from services.mission_graph_build import mission_from_steps
    from services.mission_graph_run import abort_mission
    from services.mission_graph_store import set_missions_dir_for_tests

    set_missions_dir_for_tests(tmp_path / "missions")
    mission = mission_from_steps(
        title="Abort me",
        objective="test abort",
        context="",
        tasks=[
            {
                "task_id": "t1",
                "description": "noop",
                "agent_id": "qa",
                "method": "review",
                "kwargs": {},
                "depends_on": [],
            }
        ],
        source="test",
    )
    denied = abort_mission(mission.mission_id, agent_id="dev_app", reason="nope")
    assert denied["ok"] is False
    assert denied["error"] == "capability_denied"

    ok = abort_mission(mission.mission_id, agent_id="coo", reason="stop")
    assert ok["ok"] is True
    assert ok["status"] == "CANCELLED"


def test_workflow_abort_run(trust_graph_path, tmp_path, monkeypatch: pytest.MonkeyPatch) -> None:
    from services.workflow_engine_models import StepRun, WorkflowRun
    from services.workflow_engine_run import abort_workflow_run
    from services.workflow_engine_store import save_run
    import services.workflow_engine as we

    runs_dir = tmp_path / "workflow_runs"
    runs_dir.mkdir(parents=True, exist_ok=True)
    monkeypatch.setattr(we, "_RUNS_DIR", runs_dir)
    run = WorkflowRun(
        run_id="run_test_abort",
        recipe_id="ship_app",
        status="running",
        steps=[StepRun(step_id="s1", label="one", status="PENDING")],
    )
    save_run(run)

    denied = abort_workflow_run(run.run_id, agent_id="ads", reason="no")
    assert denied["ok"] is False

    ok = abort_workflow_run(run.run_id, agent_id="coo", reason="halt")
    assert ok["ok"] is True
    assert ok["status"] == "cancelled"


def test_coding_worktree_capability(trust_graph_path) -> None:
    assert check_capability("dev_frontend", "coding:worktree")["allowed"] is True
    assert check_capability("secretary", "coding:worktree")["allowed"] is False


def test_fix_pipeline_hotfix_main(trust_graph_path) -> None:
    assert check_capability("fix_pipeline", "git:merge:main")["allowed"] is True
    assert_can_merge("fix_pipeline", "main")


def test_list_recent_trust_graph(trust_graph_path) -> None:
    from services.trust_graph import list_recent

    require_capability("dev_integrator", "git:merge:staging")
    try:
        require_capability("dev_app", "git:merge:main")
    except PermissionDeniedError:
        pass
    recent = list_recent(limit=10)
    assert len(recent) >= 2
    assert recent[0]["capability"] in {"git:merge:main", "git:merge:staging"}


def test_capabilities_api(hub_client, trust_graph_path) -> None:
    from tests.conftest import HUB_HEADERS

    r = hub_client.get("/capabilities", headers=HUB_HEADERS)
    assert r.status_code == 200
    assert any(c["id"] == "git:merge:main" for c in r.json()["capabilities"])

    p = hub_client.get("/capabilities/packs/dev_frontend", headers=HUB_HEADERS)
    assert p.status_code == 200
    caps = p.json()["capabilities"]
    assert "coding:worktree" in caps
    assert "git:merge:main" not in caps

    c = hub_client.post(
        "/permission-guard/check",
        headers=HUB_HEADERS,
        json={"agent_id": "dev_app", "capability": "git:merge:main"},
    )
    assert c.status_code == 200
    assert c.json()["allowed"] is False

    g = hub_client.get("/trust-graph/recent?limit=5", headers=HUB_HEADERS)
    assert g.status_code == 200
    assert isinstance(g.json()["decisions"], list)
