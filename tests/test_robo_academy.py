"""Tests for the Robo Academy — Eve Paper Build (SPEC_STUDIO_ACADEMIES / DEC-036).

No LLM calls: engine dispatch and QA review are monkeypatched. Workspace writes
are redirected to a tmp dir via ALNUA_WORKSPACE, progress via
ROBO_ACADEMY_PROGRESS_PATH. The gaming suite (test_gaming_academy.py) covers
the shared engine; this file covers robo-specific config + wiring.
"""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

from services import robo_academy_runner as runner_mod
from services import studio_academy_engine as engine_mod
from services import studio_academy_state as state_mod
from services.academy_curriculum_robo import LEVEL_META, all_exercises, get_exercise
from services.academy_program_robo import _AGENT_CLASSES, ROBO_PROGRAM
from services.studio_academy_gate import evaluate_gate
from services.studio_academy_program import exercise_sort_key


@pytest.fixture(autouse=True)
def isolated_state(tmp_path, monkeypatch):
    monkeypatch.setenv("ALNUA_WORKSPACE", str(tmp_path / "ws"))
    monkeypatch.setenv("ROBO_ACADEMY_PROGRESS_PATH", str(tmp_path / "progress.json"))
    monkeypatch.delenv("PI_HOST", raising=False)
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


def test_curriculum_all_workshop_roles_covered():
    agents = {e.agent_id for e in all_exercises()}
    assert agents == set(_AGENT_CLASSES)


def test_curriculum_exercises_have_dod_and_known_agent():
    for ex in all_exercises():
        assert ex.dod, f"{ex.exercise_id} missing DoD"
        assert ex.agent_id in _AGENT_CLASSES, f"{ex.exercise_id} unknown agent"
        assert ex.method, f"{ex.exercise_id} missing method"


def test_curriculum_refs_point_to_earlier_exercises():
    seen: set[str] = set()
    for ex in sorted(all_exercises(), key=exercise_sort_key):
        for ref in ex.context_refs:
            assert ref in seen, f"{ex.exercise_id} refs {ref} before it is produced"
        seen.add(ex.deliverable_path)


def test_curriculum_kwargs_match_real_method_signatures():
    """AST check: every method_kwargs key must exist in the real agent method
    signature — catches typos without importing the agent stack."""
    root = Path(__file__).resolve().parent.parent
    for ex in all_exercises():
        module, _cls = _AGENT_CLASSES[ex.agent_id]
        path = root / (module.replace(".", "/") + ".py")
        tree = ast.parse(path.read_text(encoding="utf-8"))
        methods = {
            n.name: n
            for c in ast.walk(tree)
            if isinstance(c, ast.ClassDef)
            for n in c.body
            if isinstance(n, ast.FunctionDef)
        }
        assert ex.method in methods, f"{ex.exercise_id}: {ex.agent_id}.{ex.method} not found"
        params = {a.arg for a in methods[ex.method].args.args} - {"self"}
        for kw in ex.method_kwargs:
            assert kw in params, f"{ex.exercise_id}: kwarg '{kw}' not in {ex.agent_id}.{ex.method} signature"


def test_get_exercise_lookup():
    assert get_exercise("RN1.1").agent_id == "industrial_design"
    assert get_exercise("RN9.9") is None


# ---------------------------------------------------------------------------
# Progress (generic engine, robo program)
# ---------------------------------------------------------------------------


def test_progress_default_and_record_cycle():
    data = state_mod.load_progress(ROBO_PROGRAM)
    assert data["total_exercises"] == 30
    assert data["current_level"] == 1
    assert data["program"] == "robo"

    state_mod.record_exercise_result(ROBO_PROGRAM, "RN1.2", status="in_progress")
    state_mod.record_exercise_result(ROBO_PROGRAM, "RN1.2", status="validated", qa_verdict="validated", path="meca/x.md")
    data = state_mod.load_progress(ROBO_PROGRAM)
    assert data["exercises"]["RN1.2"]["status"] == "validated"
    assert data["completed_exercises"] == 1
    assert data["success_rate_pct"] == 100.0
    assert data["levels"]["1"]["done"] == 1


def test_progress_next_pending_numeric_order():
    state_mod.record_exercise_result(ROBO_PROGRAM, "RN1.1", status="validated")
    nxt = state_mod.next_pending_exercise(ROBO_PROGRAM)
    assert nxt is not None and nxt.exercise_id == "RN1.2"


# ---------------------------------------------------------------------------
# Runner (mocked engine dispatch + QA)
# ---------------------------------------------------------------------------


class _FakeAgent:
    """Answers any agent method with a minimal valid payload."""

    def __getattr__(self, name: str):
        def _fake(**kwargs):
            return {"method": name, "summary": "livrable factice", "items": ["a", "b", "c"]}

        return _fake

    def design_form_factor(self, **kwargs):
        assert kwargs["product_name"] == "Eve — compagnon de bureau"
        return {
            "form_factor": "galet 12 cm",
            "materials": ["PC-ABS", "tissu"],
            "constraints": ["bureau 8h/jour"],
        }


def _patch_dispatch(monkeypatch, qa_verdict="validated"):
    monkeypatch.setattr(engine_mod, "_get_agent", lambda program, agent_id: _FakeAgent())
    monkeypatch.setattr(
        engine_mod,
        "_default_qa_review",
        lambda program, ex, content: {
            "verdict": qa_verdict,
            "dod_checks": [],
            "feedback": "ok" if qa_verdict == "validated" else "trop vague",
        },
    )


def test_run_exercise_end_to_end_validated(monkeypatch):
    _patch_dispatch(monkeypatch)
    result = runner_mod.run_exercise("RN1.1")
    assert result["ok"] is True
    assert result["status"] == "validated"
    assert result["path"] == "design/identite-produit.md"

    from services.rnd_workspace import read_deliverable

    content = read_deliverable("hardware", "eve-paper-build", result["path"])
    assert "galet 12 cm" in content
    assert "Eve Paper Build" in content

    data = state_mod.load_progress(ROBO_PROGRAM)
    assert data["exercises"]["RN1.1"]["status"] == "validated"


def test_run_exercise_qa_rejection_then_retry_versioned(monkeypatch):
    _patch_dispatch(monkeypatch, qa_verdict="rejected")
    first = runner_mod.run_exercise("RN1.1")
    assert first["status"] == "rejected"

    _patch_dispatch(monkeypatch, qa_verdict="validated")
    second = runner_mod.run_exercise("RN1.1")
    assert second["status"] == "validated"
    assert second["path"] == "design/identite-produit-v2.md"  # write-only, no overwrite


def test_run_next_exercise_picks_first_pending(monkeypatch):
    _patch_dispatch(monkeypatch)
    result = runner_mod.run_next_exercise()
    assert result["ok"] is True
    assert result["exercise_id"] == "RN1.1"
    assert result["status"] == "validated"


def test_default_qa_review_uses_dod_prompt(monkeypatch):
    """The engine's default QA path (robo) must call run_json_task with the DoD
    contract prompt — same review quality bar as gaming's dedicated method."""
    captured: dict = {}

    class _FakeQa:
        def run_json_task(self, **kwargs):
            captured.update(kwargs)
            return {"verdict": "validated", "dod_checks": [], "feedback": ""}

    monkeypatch.setattr(engine_mod, "_get_agent", lambda program, agent_id: _FakeQa())
    exercise = get_exercise("RN1.1")
    review = engine_mod._default_qa_review(ROBO_PROGRAM, exercise, "# contenu")
    assert review["verdict"] == "validated"
    assert captured["action"] == "review_deliverable"
    assert "Definition of Done" in captured["prompt"]
    assert "Form factor défini" in captured["prompt"]  # RN1.1 DoD item
    assert "Eve" in captured["prompt"]


# ---------------------------------------------------------------------------
# Gate
# ---------------------------------------------------------------------------


def test_gate_empty_progress_blocks():
    gate = evaluate_gate(ROBO_PROGRAM)
    assert gate["gate_open"] is False
    assert gate["readiness_pct"] == 0.0
    assert gate["success_rate_65"] is False
    assert gate["v2_prereq_pi_host"] is False


def test_gate_full_success_opens_with_pi_host(monkeypatch):
    monkeypatch.setenv("PI_HOST", "192.168.1.42")
    for ex in all_exercises():
        state_mod.record_exercise_result(ROBO_PROGRAM, ex.exercise_id, status="validated")
    gate = evaluate_gate(ROBO_PROGRAM)
    assert gate["success_rate_65"] is True
    assert gate["n3_prototype_complete"] is True
    assert gate["roles_coverage_10"] is True
    assert gate["canon_clean"] is True
    assert gate["v2_prereq_pi_host"] is True
    assert gate["gate_open"] is True
    assert gate["readiness_pct"] == 100.0


# ---------------------------------------------------------------------------
# 49.2 — Idle integration + endpoints
# ---------------------------------------------------------------------------


def test_day_plan_includes_robo_academy_items(tmp_path, monkeypatch):
    monkeypatch.setattr("services.idle_work_queue._QUEUE_PATH", tmp_path / "idle_queue.json")
    from services.idle_work_queue import build_day_plan

    queue = build_day_plan(autonomy_level=1)
    robo = [i for i in queue["items"] if i["kind"] == "robo_academy_exercise"]
    assert len(robo) == 2
    for item in robo:
        assert item["level"] == 1
        assert item["family"] == "robo"
        assert item["status"] == "pending"


def test_day_plan_autonomy_l0_excludes_robo(tmp_path, monkeypatch):
    monkeypatch.setattr("services.idle_work_queue._QUEUE_PATH", tmp_path / "idle_queue.json")
    from services.idle_work_queue import build_day_plan

    queue = build_day_plan(autonomy_level=0)
    assert not [i for i in queue["items"] if i["kind"] == "robo_academy_exercise"]


def test_robo_item_deferred_on_budget_warning():
    from services.idle_work_queue import _item_eligible

    item = {"status": "pending", "level": 1, "kind": "robo_academy_exercise", "family": "robo"}
    assert _item_eligible(item, {}, "warning") == "budget_warning_deferred"
    assert _item_eligible(item, {}, "ok") is None


def test_recipe_executes_robo_academy_kind(tmp_path, monkeypatch):
    monkeypatch.setattr("services.idle_work_recipes._DELIVERABLES", tmp_path / "deliv")
    marked: list[dict] = []
    monkeypatch.setattr("services.idle_work_queue.mark_item", lambda *a, **kw: marked.append(kw))
    monkeypatch.setattr(
        runner_mod,
        "run_next_exercise",
        lambda: {"ok": True, "exercise_id": "RN1.1", "status": "validated", "path": "design/x.md"},
    )
    from services.idle_work_recipes import _execute_one

    result = _execute_one(
        {"id": "idle_test_robo", "kind": "robo_academy_exercise", "agent_id": "industrial_design", "title": "t"},
        "run-1",
    )
    assert result["ok"] is True
    assert "RN1.1" in result["detail"]
    assert "robo academy" in result["detail"]
    assert marked and marked[0]["status"] == "done"


def test_router_endpoints(monkeypatch):
    from api.routers import robo_academy as router_mod_ra

    monkeypatch.setattr(runner_mod, "studio_status", lambda: {"subject": "Eve", "completed": 1})
    assert router_mod_ra.robo_academy_status()["subject"] == "Eve"

    monkeypatch.setattr(runner_mod, "run_exercise", lambda eid: {"ok": True, "exercise_id": eid})
    assert router_mod_ra.robo_academy_run("RN1.1")["exercise_id"] == "RN1.1"

    curriculum = router_mod_ra.robo_academy_curriculum(level=1)
    assert curriculum["count"] == 10
    assert all(e["level"] == 1 for e in curriculum["exercises"])
    assert curriculum["exercises"][0]["id"] == "RN1.1"  # numeric sort

    gate = router_mod_ra.robo_academy_gate()
    assert "gate_open" in gate and "readiness_pct" in gate
