"""Review Chain — Phase D (DEC-025)."""

from __future__ import annotations

import pytest

from services.merge_policy import merge_autonomy
from services.review_chain import run_review_chain
from services.review_chain_models import GateResult


def test_auto_fail_stops_before_board() -> None:
    def bad() -> GateResult:
        return GateResult(gate="AUTO", outcome="fail", feedback="pytest failed: assert 1==2")

    result = run_review_chain(
        department="app",
        artifact={"title": "x", "body": "y" * 50, "status": "ready"},
        auto_checks=[bad],
        merge_agent_id="dev_integrator",
        target_branch="staging",
        dry_run=True,
    )
    assert result.status == "REJECTED"
    assert result.gates[0].gate == "AUTO"
    assert result.gates[0].outcome == "fail"
    assert all(g.gate != "BOARD" for g in result.gates[1:])
    assert "pytest failed" in result.feedback_log[0]


def test_main_requires_human() -> None:
    result = run_review_chain(
        department="app",
        artifact={"title": "Ship", "body": "desc " * 20, "status": "ready", "project_id": "hub"},
        producer_agent_id="dev_app",
        merge_agent_id="dev_integrator",
        target_branch="main",
        auto_preapproved=True,
        board_preapproved=True,
        dry_run=True,
    )
    assert result.status == "A_VERIFIER"
    assert result.merge_mode == "human_required"


def test_staging_auto_with_trust(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("REVIEW_CHAIN_STAGING_TRUST_MIN", "0.70")
    try:
        from config.settings import get_settings

        get_settings.cache_clear()
    except Exception:
        pass

    monkeypatch.setattr(
        "services.merge_policy._producer_trust_score",
        lambda _aid: 0.85,
    )
    result = run_review_chain(
        department="app",
        artifact={"title": "Ship", "body": "desc " * 20, "status": "ready", "project_id": "hub"},
        producer_agent_id="dev_app",
        merge_agent_id="dev_integrator",
        target_branch="staging",
        auto_preapproved=True,
        board_preapproved=True,
        dry_run=True,
    )
    assert result.status == "APPROVED"
    assert result.merge_mode == "auto"


def test_integrate_required_for_multi_branch() -> None:
    calls = {"n": 0}

    def fake_integrate(**kwargs):
        calls["n"] += 1
        return {"status": "ok", "merged": kwargs.get("worktrees") or [], "conflicts": []}

    result = run_review_chain(
        department="app",
        artifact={"title": "Multi", "body": "desc " * 20, "status": "ready", "project_id": "hub"},
        producer_agent_id="dev_app",
        merge_agent_id="dev_integrator",
        target_branch="staging",
        feature_branches=["feat/a", "feat/b"],
        repo_path="/tmp/repo",
        auto_preapproved=True,
        board_preapproved=True,
        dry_run=False,
        integrate_fn=fake_integrate,
        human_approved=True,  # skip trust variance
    )
    assert result.status == "APPROVED"
    assert calls["n"] == 1
    integ = next(g for g in result.gates if g.gate == "INTEGRATE")
    assert integ.outcome == "pass"


def test_integrate_conflicts_fail_with_feedback() -> None:
    def conflict_integrate(**kwargs):
        return {
            "status": "conflict",
            "merged": [],
            "conflicts": [{"branch": "feat/b", "error": "CONFLICT in web/page.tsx"}],
        }

    result = run_review_chain(
        department="app",
        artifact={"title": "Multi", "body": "desc " * 20, "status": "ready", "project_id": "hub"},
        merge_agent_id="dev_integrator",
        target_branch="staging",
        feature_branches=["feat/a", "feat/b"],
        repo_path="/tmp/repo",
        auto_preapproved=True,
        board_preapproved=True,
        human_approved=True,
        dry_run=False,
        integrate_fn=conflict_integrate,
    )
    assert result.status == "INTEGRATE_FAILED"
    assert "CONFLICT" in (result.feedback_log[-1] if result.feedback_log else "")


def test_merge_autonomy_rules() -> None:
    assert merge_autonomy("main")["mode"] == "human_required"
    assert merge_autonomy("staging", repo_slug="academy")["mode"] == "auto"
    assert merge_autonomy("staging", department="ads")["mode"] == "human_required"
    assert (
        merge_autonomy("main", actor_agent_id="fix_pipeline")["mode"] == "auto"
    )


def test_ensure_integrate_task(tmp_path, monkeypatch: pytest.MonkeyPatch) -> None:
    from services.mission_graph_build import ensure_integrate_task, mission_from_steps

    monkeypatch.setattr(
        "services.mission_graph_store._missions_dir",
        lambda: tmp_path,
    )
    mission = mission_from_steps(
        title="pair",
        tasks=[
            {
                "task_id": "1",
                "description": "API",
                "agent_id": "dev_backend",
                "method": "implement",
            },
            {
                "task_id": "2",
                "description": "UI",
                "agent_id": "dev_frontend",
                "method": "implement",
            },
        ],
        persist=True,
    )
    task = ensure_integrate_task(mission, persist=True)
    assert task is not None
    assert task.agent_id == "dev_integrator"
    assert set(task.depends_on) == {"1", "2"}


def test_mission_ship_recipe_registered() -> None:
    from services.workflow_engine_catalog import get_recipe

    r = get_recipe("mission_ship")
    assert r is not None
    ids = [s.id for s in r.steps]
    assert "review_chain" in ids
    assert "require_integrate" in ids


def test_e2e_two_prs_integrate_staging_dry(tmp_path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Acceptance dry-run: 2 feature PRs → integrate → staging auto merge path."""
    from services.merge_policy import assert_can_merge
    from services.mission_graph_build import ensure_integrate_task, mission_from_steps
    from services.mission_graph_store import set_missions_dir_for_tests
    from services.permission_guard import check_capability
    from services.workflow_step_handlers_review import (
        _step_require_integrate,
        _step_review_chain,
    )

    set_missions_dir_for_tests(tmp_path / "missions")
    monkeypatch.setenv("PERMISSION_GUARD_ENABLED", "1")
    monkeypatch.setenv("REVIEW_CHAIN_STAGING_TRUST_MIN", "0.70")
    try:
        from config.settings import get_settings

        get_settings.cache_clear()
    except Exception:
        pass
    monkeypatch.setattr(
        "services.merge_policy._producer_trust_score",
        lambda _aid: 0.92,
    )

    mission = mission_from_steps(
        title="E2E two PRs",
        objective="Ship API + UI to staging",
        tasks=[
            {
                "task_id": "pr_api",
                "description": "API feature PR",
                "agent_id": "dev_backend",
                "method": "implement",
                "kwargs": {"branch": "feat/api-auth"},
            },
            {
                "task_id": "pr_ui",
                "description": "UI feature PR",
                "agent_id": "dev_frontend",
                "method": "implement",
                "kwargs": {"branch": "feat/ui-auth"},
            },
        ],
        persist=True,
    )
    integ_task = ensure_integrate_task(mission, target_branch="staging", persist=True)
    assert integ_task is not None
    assert integ_task.agent_id == "dev_integrator"
    assert set(integ_task.depends_on) == {"pr_api", "pr_ui"}

    branches = ["feat/api-auth", "feat/ui-auth"]
    integrate_calls: list[dict] = []

    def fake_integrate(**kwargs):
        integrate_calls.append(kwargs)
        return {
            "status": "ok",
            "merged": list(kwargs.get("worktrees") or []),
            "conflicts": [],
            "branch": kwargs.get("branch"),
        }

    chain = run_review_chain(
        department="app",
        artifact={
            "title": "Auth ship",
            "body": "Two PRs ready for staging " * 5,
            "status": "ready",
            "project_id": "hub",
        },
        producer_agent_id="dev_backend",
        merge_agent_id="dev_integrator",
        target_branch="staging",
        repo_slug="hub",
        repo_path=str(tmp_path / "repo"),
        feature_branches=branches,
        integration_branch="integrate/e2e-auth",
        auto_preapproved=True,
        board_preapproved=True,
        dry_run=False,
        integrate_fn=fake_integrate,
    )
    assert chain.status == "APPROVED"
    assert chain.merge_mode == "auto"
    assert [g.gate for g in chain.gates] == ["AUTO", "BOARD", "POLICY", "INTEGRATE", "DONE"]
    assert all(g.outcome == "pass" for g in chain.gates)
    assert integrate_calls and integrate_calls[0]["worktrees"] == branches
    assert_can_merge("dev_integrator", "staging", repo_slug="hub")
    assert check_capability("dev_integrator", "github:pr:merge")["allowed"] is True
    assert check_capability("dev_frontend", "git:merge:staging")["allowed"] is False

    # Workflow steps share context: review_chain → require_integrate (dry_run).
    ctx: dict = {
        "department": "app",
        "slug": "hub",
        "title": "Auth ship",
        "summary": "Two PRs ready for staging " * 5,
        "producer_agent_id": "dev_backend",
        "merge_agent_id": "dev_integrator",
        "target_branch": "staging",
        "repo_slug": "hub",
        "feature_branches": branches,
        "auto_preapproved": True,
        "board_preapproved": True,
        "dry_run": True,
    }
    step1 = _step_review_chain(ctx)
    assert step1["status"] == "OK"
    assert ctx.get("_review_chain", {}).get("status") == "APPROVED"
    assert ctx.get("integrate_done") is True
    step2 = _step_require_integrate(ctx)
    assert step2["status"] == "OK"


def test_e2e_mission_ship_workflow_dry(tmp_path, monkeypatch: pytest.MonkeyPatch) -> None:
    """mission_ship recipe dry-run with 2 branches completes without git."""
    from types import SimpleNamespace

    from services.workflow_engine import run_workflow

    monkeypatch.setenv("REVIEW_CHAIN_STAGING_TRUST_MIN", "0.70")
    try:
        from config.settings import get_settings

        get_settings.cache_clear()
    except Exception:
        pass
    monkeypatch.setattr(
        "services.merge_policy._producer_trust_score",
        lambda _aid: 0.9,
    )
    monkeypatch.setattr(
        "services.company_errors.count_open_errors",
        lambda **_kw: 0,
    )
    monkeypatch.setattr(
        "services.company_errors.list_open_errors",
        lambda **_kw: [],
    )
    fake_app = SimpleNamespace(
        slug="hub",
        name="ALNUA Hub",
        branch="hub",
        github_repo="org/hub",
        local_path=str(tmp_path),
        description="test",
        stack="python",
        prod_url="",
        enabled=True,
        lifecycle_status="build",
    )
    monkeypatch.setattr("services.app_registry.get_app", lambda _slug: fake_app)
    monkeypatch.setattr(
        "services.app_registry.upsert_app",
        lambda *_a, **_k: fake_app,
    )

    import services.workflow_engine as we

    runs_dir = tmp_path / "workflow_runs"
    runs_dir.mkdir(parents=True, exist_ok=True)
    monkeypatch.setattr(we, "_RUNS_DIR", runs_dir)

    out = run_workflow(
        "mission_ship",
        {
            "slug": "hub",
            "department": "app",
            "title": "E2E mission ship",
            "summary": "Two feature branches to staging " * 4,
            "producer_agent_id": "dev_app",
            "feature_branches": ["feat/a", "feat/b"],
            "target_branch": "staging",
            "auto_preapproved": True,
            "board_preapproved": True,
            "dry_run": True,
            "max_open_errors": 99,
            "target_status": "beta",
        },
    )
    assert out.get("success") is True or out.get("status") == "completed"
    assert out.get("blocked") is not True
    step_ids = [s.get("step_id") or s.get("id") for s in (out.get("steps") or [])]
    assert "review_chain" in step_ids
    assert "require_integrate" in step_ids
    rc = next(s for s in out["steps"] if (s.get("step_id") or s.get("id")) == "review_chain")
    assert rc.get("status") in {"OK", "A_VERIFIER"}
    if rc.get("status") == "OK":
        result = (rc.get("result") or {})
        assert result.get("status") == "APPROVED"
        assert [g["gate"] for g in result.get("gates") or []] == [
            "AUTO",
            "BOARD",
            "POLICY",
            "INTEGRATE",
            "DONE",
        ]