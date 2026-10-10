"""Tests for the Comms Academy — Lancement NAÏA (SPEC_STUDIO_ACADEMIES / DEC-036).

No LLM calls: engine dispatch and QA review are monkeypatched. Workspace writes
are redirected to a tmp dir via ALNUA_WORKSPACE, progress via
COMMS_ACADEMY_PROGRESS_PATH. The gaming/robo suites cover the shared engine;
this file covers comms-specific config + the side-effect discipline (no
production-table writes from academy exercises).
"""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

from services import comms_academy_runner as runner_mod
from services import studio_academy_engine as engine_mod
from services import studio_academy_state as state_mod
from services.academy_curriculum_comms import LEVEL_META, all_exercises, get_exercise
from services.academy_program_comms import _AGENT_CLASSES, COMMS_PROGRAM
from services.studio_academy_gate import evaluate_gate
from services.studio_academy_program import exercise_sort_key

# Methods that write to production tables (posts queue, campaigns, dossier
# assets) — the academy must NEVER call them (DEC-036 side-effect discipline).
_FORBIDDEN_METHODS = {
    "create_campaign",
    "amplify_post",
    "generate_posts",
    "generate_from_dev_logs",
    "approve_post",
    "update_post",
    "draft_from_dev_log",
    "draft_hype_posts",
    "draft_build_in_public",
    "draft_corporate_announcement",
    "post_devlog_to_discord",
    "generate_assets",
    "generate_kit",
}


@pytest.fixture(autouse=True)
def isolated_state(tmp_path, monkeypatch):
    monkeypatch.setenv("ALNUA_WORKSPACE", str(tmp_path / "ws"))
    monkeypatch.setenv("COMMS_ACADEMY_PROGRESS_PATH", str(tmp_path / "progress.json"))
    monkeypatch.delenv("PROJECT_ID_NAIA", raising=False)
    return tmp_path


# ---------------------------------------------------------------------------
# Curriculum integrity
# ---------------------------------------------------------------------------


def test_curriculum_has_30_unique_exercises():
    exercises = all_exercises()
    assert len(exercises) == 30
    assert len({e.exercise_id for e in exercises}) == 30
    assert len({e.deliverable_path for e in exercises}) == 30


def test_curriculum_levels_match_meta():
    counts: dict[int, int] = {}
    for ex in all_exercises():
        assert 1 <= ex.level <= 4
        counts[ex.level] = counts.get(ex.level, 0) + 1
    for lv, meta in LEVEL_META.items():
        assert counts.get(lv, 0) == int(meta["exercises"]), f"level {lv} count mismatch"


def test_curriculum_all_comms_roles_covered():
    agents = {e.agent_id for e in all_exercises()}
    assert agents == set(_AGENT_CLASSES)


def test_curriculum_never_touches_production_side_effects():
    """Academy exercises must be paper-only: no posts queued, no campaigns
    created, no assets generated (DEC-036)."""
    for ex in all_exercises():
        assert ex.method not in _FORBIDDEN_METHODS, (
            f"{ex.exercise_id} uses side-effecting method {ex.method} — forbidden in academy"
        )


def test_curriculum_refs_point_to_earlier_exercises():
    seen: set[str] = set()
    for ex in sorted(all_exercises(), key=exercise_sort_key):
        for ref in ex.context_refs:
            assert ref in seen, f"{ex.exercise_id} refs {ref} before it is produced"
        seen.add(ex.deliverable_path)


def test_curriculum_kwargs_match_real_method_signatures():
    """AST check: every method_kwargs key must exist in the real method
    signature — run_json_task resolved on AgentBase (inherited by content_*)."""
    root = Path(__file__).resolve().parent.parent

    def methods_of(module: str) -> dict[str, ast.FunctionDef]:
        path = root / (module.replace(".", "/") + ".py")
        tree = ast.parse(path.read_text(encoding="utf-8"))
        return {
            n.name: n
            for c in ast.walk(tree)
            if isinstance(c, ast.ClassDef)
            for n in c.body
            if isinstance(n, ast.FunctionDef)
        }

    base_methods = methods_of("agents.agent_base")
    for ex in all_exercises():
        module, _cls = _AGENT_CLASSES[ex.agent_id]
        methods = methods_of(module)
        node = methods.get(ex.method) or base_methods.get(ex.method)
        assert node is not None, f"{ex.exercise_id}: {ex.agent_id}.{ex.method} not found"
        params = {a.arg for a in node.args.args} | {a.arg for a in node.args.kwonlyargs}
        params -= {"self"}
        for kw in ex.method_kwargs:
            assert kw in params, f"{ex.exercise_id}: kwarg '{kw}' not in {ex.agent_id}.{ex.method} signature"


def test_get_exercise_lookup():
    assert get_exercise("CN1.1").agent_id == "marketing"
    assert get_exercise("CN9.9") is None


# ---------------------------------------------------------------------------
# Runner (mocked engine dispatch + QA)
# ---------------------------------------------------------------------------


class _FakeAgent:
    """Answers any agent method with a minimal valid payload."""

    def __getattr__(self, name: str):
        def _fake(**kwargs):
            return {"method": name, "summary": "livrable factice", "items": ["a", "b", "c"]}

        return _fake

    def handle_instruction(self, instruction: str):
        # Real MarketingAgent.handle_instruction returns str — engine wraps it.
        assert "NAÏA" in instruction
        return "Stratégie factice : positionnement, audiences, phasage."


def _patch_dispatch(monkeypatch, qa_verdict="validated"):
    monkeypatch.setattr(engine_mod, "_get_agent", lambda program, agent_id: _FakeAgent())
    monkeypatch.setattr(
        engine_mod,
        "_default_qa_review",
        lambda program, ex, content: {
            "verdict": qa_verdict,
            "dod_checks": [],
            "feedback": "ok" if qa_verdict == "validated" else "hors ton NAÏA",
        },
    )


def test_run_exercise_end_to_end_validated(monkeypatch):
    _patch_dispatch(monkeypatch)
    result = runner_mod.run_exercise("CN1.1")
    assert result["ok"] is True
    assert result["status"] == "validated"
    assert result["path"] == "strategy/strategie-lancement.md"

    from services.rnd_workspace import read_deliverable

    content = read_deliverable("comms", "naia-launch", result["path"])
    assert "Stratégie factice" in content
    assert "Lancement NAÏA" in content

    data = state_mod.load_progress(COMMS_PROGRAM)
    assert data["exercises"]["CN1.1"]["status"] == "validated"


def test_run_exercise_qa_rejection_then_retry_versioned(monkeypatch):
    _patch_dispatch(monkeypatch, qa_verdict="rejected")
    first = runner_mod.run_exercise("CN1.1")
    assert first["status"] == "rejected"

    _patch_dispatch(monkeypatch, qa_verdict="validated")
    second = runner_mod.run_exercise("CN1.1")
    assert second["status"] == "validated"
    assert second["path"] == "strategy/strategie-lancement-v2.md"


def test_run_next_exercise_picks_first_pending(monkeypatch):
    _patch_dispatch(monkeypatch)
    result = runner_mod.run_next_exercise()
    assert result["ok"] is True
    assert result["exercise_id"] == "CN1.1"
    assert result["status"] == "validated"


def test_run_json_task_kwargs_built(monkeypatch):
    """run_json_task exercises (content_* sectors) get action/prompt/learning_key
    from the engine — the shared AgentBase path replaces side-effecting methods."""
    captured: dict = {}

    class _RecordingAgent:
        def run_json_task(self, **kwargs):
            captured.update(kwargs)
            return {"sections": ["a", "b"]}

    monkeypatch.setattr(engine_mod, "_get_agent", lambda program, agent_id: _RecordingAgent())
    _patch_dispatch(monkeypatch)
    monkeypatch.setattr(engine_mod, "_get_agent", lambda program, agent_id: _RecordingAgent())
    result = runner_mod.run_exercise("CN1.3")  # content_app / run_json_task
    assert result["status"] == "validated"
    assert captured["action"] == "academy_exercise"
    assert "calendrier éditorial" in captured["prompt"].lower()
    assert captured["learning_key"]


# ---------------------------------------------------------------------------
# Gate
# ---------------------------------------------------------------------------


def test_gate_empty_progress_blocks():
    gate = evaluate_gate(COMMS_PROGRAM)
    assert gate["gate_open"] is False
    assert gate["readiness_pct"] == 0.0
    assert gate["v2_prereq_naia_project"] is False


def test_gate_full_success_opens_with_naia_project(monkeypatch):
    monkeypatch.setenv("PROJECT_ID_NAIA", "proj-naia-123")
    for ex in all_exercises():
        state_mod.record_exercise_result(COMMS_PROGRAM, ex.exercise_id, status="validated")
    gate = evaluate_gate(COMMS_PROGRAM)
    assert gate["success_rate_65"] is True
    assert gate["n3_campaign_complete"] is True
    assert gate["roles_coverage_10"] is True
    assert gate["canon_clean"] is True
    assert gate["v2_prereq_naia_project"] is True
    assert gate["gate_open"] is True


# ---------------------------------------------------------------------------
# 49.3 — Idle integration + endpoints
# ---------------------------------------------------------------------------


def test_day_plan_includes_comms_academy_items(tmp_path, monkeypatch):
    monkeypatch.setattr("services.idle_work_queue._QUEUE_PATH", tmp_path / "idle_queue.json")
    from services.idle_work_queue import build_day_plan

    queue = build_day_plan(autonomy_level=1)
    comms = [i for i in queue["items"] if i["kind"] == "comms_academy_exercise"]
    assert len(comms) == 2
    for item in comms:
        assert item["level"] == 1
        assert item["family"] == "comms"
        assert item["status"] == "pending"


def test_comms_item_deferred_on_budget_warning():
    from services.idle_work_queue import _item_eligible

    item = {"status": "pending", "level": 1, "kind": "comms_academy_exercise", "family": "comms"}
    assert _item_eligible(item, {}, "warning") == "budget_warning_deferred"
    assert _item_eligible(item, {}, "ok") is None


def test_recipe_executes_comms_academy_kind(tmp_path, monkeypatch):
    monkeypatch.setattr("services.idle_work_recipes._DELIVERABLES", tmp_path / "deliv")
    marked: list[dict] = []
    monkeypatch.setattr("services.idle_work_queue.mark_item", lambda *a, **kw: marked.append(kw))
    monkeypatch.setattr(
        runner_mod,
        "run_next_exercise",
        lambda: {"ok": True, "exercise_id": "CN1.1", "status": "validated", "path": "strategy/x.md"},
    )
    from services.idle_work_recipes import _execute_one

    result = _execute_one(
        {"id": "idle_test_comms", "kind": "comms_academy_exercise", "agent_id": "marketing", "title": "t"},
        "run-1",
    )
    assert result["ok"] is True
    assert "CN1.1" in result["detail"]
    assert "comms academy" in result["detail"]
    assert marked and marked[0]["status"] == "done"


def test_router_endpoints(monkeypatch):
    from api.routers import comms_academy as router_mod_ca

    monkeypatch.setattr(runner_mod, "studio_status", lambda: {"subject": "NAÏA", "completed": 1})
    assert router_mod_ca.comms_academy_status()["subject"] == "NAÏA"

    monkeypatch.setattr(runner_mod, "run_exercise", lambda eid: {"ok": True, "exercise_id": eid})
    assert router_mod_ca.comms_academy_run("CN1.1")["exercise_id"] == "CN1.1"

    curriculum = router_mod_ca.comms_academy_curriculum(level=1)
    assert curriculum["count"] == 10
    assert all(e["level"] == 1 for e in curriculum["exercises"])
    assert curriculum["exercises"][0]["id"] == "CN1.1"

    gate = router_mod_ca.comms_academy_gate()
    assert "gate_open" in gate and "readiness_pct" in gate
