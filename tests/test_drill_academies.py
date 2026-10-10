"""Tests for the 49.4 drill academies — analytics, finance, rnd (DEC-036).

No LLM calls: engine dispatch and QA review are monkeypatched. Workspace writes
are redirected to a tmp dir via ALNUA_WORKSPACE, progress via each program's
env var. Structure mirrors test_robo_academy.py, parametrized over the three
drill programs; the gaming suite covers the shared engine internals.
"""

from __future__ import annotations

import ast
from datetime import date
from pathlib import Path

import pytest

from services import studio_academy_engine as engine_mod
from services import studio_academy_state as state_mod
from services.academy_program_analytics import _AGENT_CLASSES as ANALYTICS_CLASSES
from services.academy_program_analytics import ANALYTICS_PROGRAM
from services.academy_program_finance import _AGENT_CLASSES as FINANCE_CLASSES
from services.academy_program_finance import FINANCE_PROGRAM
from services.academy_program_rnd import _AGENT_CLASSES as RND_CLASSES
from services.academy_program_rnd import RND_PROGRAM
from services.studio_academy_gate import evaluate_gate
from services.studio_academy_program import exercise_sort_key, get_program

PROGRAMS = [ANALYTICS_PROGRAM, FINANCE_PROGRAM, RND_PROGRAM]
CLASSES = {
    "analytics": ANALYTICS_CLASSES,
    "finance": FINANCE_CLASSES,
    "rnd": RND_CLASSES,
}
FIRST_IDS = {"analytics": "AN1.1", "finance": "FN1.1", "rnd": "RD1.1"}

# Read-only allowlists — drill exercises must never touch production-writing
# methods (same discipline as comms, DEC-036).
ALLOWED_METHODS = {
    "analytics": {"define_kpis", "sql_query", "market_analysis", "user_research", "strategic_brief", "anomaly_report"},
    "finance": {"financial_advice", "analyze_costs", "build_forecast", "monthly_report", "list_open_invoices"},
    "rnd": {"run_json_task"},
}


@pytest.fixture(autouse=True)
def isolated_state(tmp_path, monkeypatch):
    monkeypatch.setenv("ALNUA_WORKSPACE", str(tmp_path / "ws"))
    monkeypatch.setenv("ANALYTICS_ACADEMY_PROGRESS_PATH", str(tmp_path / "analytics.json"))
    monkeypatch.setenv("FINANCE_ACADEMY_PROGRESS_PATH", str(tmp_path / "finance.json"))
    monkeypatch.setenv("RND_ACADEMY_PROGRESS_PATH", str(tmp_path / "rnd.json"))
    return tmp_path


# ---------------------------------------------------------------------------
# Curriculum integrity (all three drills)
# ---------------------------------------------------------------------------


def test_curriculum_10_unique_exercises_per_drill():
    for program in PROGRAMS:
        exercises = program.exercises()
        assert len(exercises) == 10, program.program_id
        assert len({e.exercise_id for e in exercises}) == 10
        assert len({e.deliverable_path for e in exercises}) == 10


def test_curriculum_levels_match_meta():
    for program in PROGRAMS:
        counts: dict[int, int] = {}
        for ex in program.exercises():
            assert 1 <= ex.level <= 3
            counts[ex.level] = counts.get(ex.level, 0) + 1
        for lv, meta in program.level_meta.items():
            assert counts.get(lv, 0) == int(meta["exercises"]), f"{program.program_id} level {lv} mismatch"


def test_curriculum_roles_and_dod():
    for program in PROGRAMS:
        classes = CLASSES[program.program_id]
        for ex in program.exercises():
            assert ex.dod, f"{ex.exercise_id} missing DoD"
            assert ex.agent_id in classes, f"{ex.exercise_id} unknown agent"
            assert ex.method, f"{ex.exercise_id} missing method"
        # Every trainee role gets at least one exercise.
        exercised = {e.agent_id for e in program.exercises()}
        assert set(program.studio_roles) <= exercised, program.program_id


def test_curriculum_refs_point_to_earlier_exercises():
    for program in PROGRAMS:
        seen: set[str] = set()
        for ex in sorted(program.exercises(), key=exercise_sort_key):
            for ref in ex.context_refs:
                assert ref in seen, f"{ex.exercise_id} refs {ref} before it is produced"
            seen.add(ex.deliverable_path)


def test_curriculum_kwargs_match_real_method_signatures():
    """AST check: every method_kwargs key must exist in the real agent method
    signature. run_json_task is inherited — check it on AgentBase instead."""
    root = Path(__file__).resolve().parent.parent
    for program in PROGRAMS:
        classes = CLASSES[program.program_id]
        for ex in program.exercises():
            module, _cls = classes[ex.agent_id]
            if ex.method == "run_json_task":
                path = root / "agents/agent_base.py"
            else:
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


def test_drills_never_touch_production_side_effects():
    """Guard rail (DEC-036): drills stick to read-only / paper methods."""
    for program in PROGRAMS:
        allowed = ALLOWED_METHODS[program.program_id]
        for ex in program.exercises():
            assert ex.method in allowed, f"{ex.exercise_id}: method {ex.method} not in read-only allowlist"


def test_qa_agent_registered_in_classes():
    for program in PROGRAMS:
        assert program.qa_agent_id in CLASSES[program.program_id]


def test_program_registry_includes_drills():
    for pid in ("analytics", "finance", "rnd"):
        assert get_program(pid).program_id == pid


# ---------------------------------------------------------------------------
# Runner (mocked engine dispatch + QA)
# ---------------------------------------------------------------------------


class _FakeAgent:
    def __getattr__(self, name: str):
        def _fake(**kwargs):
            return {"method": name, "summary": "livrable factice", "items": ["a", "b", "c"]}

        return _fake


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
    import importlib

    _patch_dispatch(monkeypatch)
    for program in PROGRAMS:
        runner = importlib.import_module(program.runner_module)
        result = runner.run_exercise(FIRST_IDS[program.program_id])
        assert result["ok"] is True, program.program_id
        assert result["status"] == "validated"
        data = state_mod.load_progress(program)
        assert data["exercises"][FIRST_IDS[program.program_id]]["status"] == "validated"


def test_run_next_exercise_picks_first_pending(monkeypatch):
    import importlib

    _patch_dispatch(monkeypatch)
    for program in PROGRAMS:
        runner = importlib.import_module(program.runner_module)
        result = runner.run_next_exercise()
        assert result["ok"] is True
        assert result["exercise_id"] == FIRST_IDS[program.program_id]


def test_default_qa_review_uses_program_qa_agent(monkeypatch):
    """The engine's default QA path must call the program's QA agent via
    run_json_task with the DoD contract prompt."""
    seen: dict[str, str] = {}

    class _FakeQa:
        def run_json_task(self, **kwargs):
            seen["prompt"] = kwargs["prompt"]
            return {"verdict": "validated", "dod_checks": [], "feedback": ""}

    captured_agents: list[str] = []
    monkeypatch.setattr(
        engine_mod, "_get_agent",
        lambda program, agent_id: (captured_agents.append(agent_id), _FakeQa())[1],
    )
    for program in PROGRAMS:
        exercise = program.exercises()[0]
        review = engine_mod._default_qa_review(program, exercise, "# contenu")
        assert review["verdict"] == "validated"
        assert captured_agents[-1] == program.qa_agent_id
        assert "Definition of Done" in seen["prompt"]


# ---------------------------------------------------------------------------
# Gate
# ---------------------------------------------------------------------------


def test_gate_empty_progress_blocks_but_training_only_ok():
    for program in PROGRAMS:
        gate = evaluate_gate(program)
        assert gate["gate_open"] is False
        assert gate["training_only_no_prod_gate"] is True


# ---------------------------------------------------------------------------
# 49.4 — Idle integration + endpoints
# ---------------------------------------------------------------------------


class _Monday(date):
    @classmethod
    def today(cls):
        return cls(2026, 10, 12)  # Monday


class _Tuesday(date):
    @classmethod
    def today(cls):
        return cls(2026, 10, 13)  # Tuesday


def _build(monkeypatch, tmp_path, fake_date):
    monkeypatch.setattr("services.idle_work_queue._QUEUE_PATH", tmp_path / "idle_queue.json")
    monkeypatch.setattr("services.idle_work_plan.date", fake_date)
    from services.idle_work_queue import build_day_plan

    return build_day_plan(autonomy_level=1)


def test_day_plan_includes_analytics_and_finance_items(monkeypatch, tmp_path):
    queue = _build(monkeypatch, tmp_path, _Tuesday)
    for kind, family in (("analytics_academy_exercise", "analytics"), ("finance_academy_exercise", "finance")):
        items = [i for i in queue["items"] if i["kind"] == kind]
        assert len(items) == 2, kind
        for item in items:
            assert item["level"] == 1
            assert item["family"] == family
            assert item["status"] == "pending"


def test_day_plan_rnd_items_monday_only(monkeypatch, tmp_path):
    monday = _build(monkeypatch, tmp_path, _Monday)
    assert len([i for i in monday["items"] if i["kind"] == "rnd_academy_exercise"]) == 2

    tuesday = _build(monkeypatch, tmp_path, _Tuesday)
    assert not [i for i in tuesday["items"] if i["kind"] == "rnd_academy_exercise"]


def test_day_plan_autonomy_l0_excludes_drills(monkeypatch, tmp_path):
    monkeypatch.setattr("services.idle_work_queue._QUEUE_PATH", tmp_path / "idle_queue.json")
    monkeypatch.setattr("services.idle_work_plan.date", _Monday)
    from services.idle_work_queue import build_day_plan

    queue = build_day_plan(autonomy_level=0)
    for kind in ("analytics_academy_exercise", "finance_academy_exercise", "rnd_academy_exercise"):
        assert not [i for i in queue["items"] if i["kind"] == kind]


def test_drill_items_deferred_on_budget_warning():
    from services.idle_work_queue import _item_eligible

    for family in ("analytics", "finance", "rnd"):
        item = {"status": "pending", "level": 1, "kind": f"{family}_academy_exercise", "family": family}
        assert _item_eligible(item, {}, "warning") == "budget_warning_deferred"
        assert _item_eligible(item, {}, "ok") is None


def test_recipe_executes_drill_kinds(monkeypatch, tmp_path):
    import importlib

    monkeypatch.setattr("services.idle_work_recipes._DELIVERABLES", tmp_path / "deliv")
    marked: list[dict] = []
    monkeypatch.setattr("services.idle_work_queue.mark_item", lambda *a, **kw: marked.append(kw))
    from services.idle_work_recipes import _execute_one

    for program in PROGRAMS:
        runner = importlib.import_module(program.runner_module)
        first = FIRST_IDS[program.program_id]
        monkeypatch.setattr(
            runner,
            "run_next_exercise",
            lambda *a, _f=first, **kw: {"ok": True, "exercise_id": _f, "status": "validated", "path": "x/y.md"},
        )
        marked.clear()
        result = _execute_one(
            {"id": f"idle_test_{program.program_id}", "kind": f"{program.program_id}_academy_exercise",
             "agent_id": program.studio_roles[0], "title": "t"},
            "run-1",
        )
        assert result["ok"] is True, program.program_id
        assert first in result["detail"]
        assert marked and marked[0]["status"] == "done"


def test_router_endpoints(monkeypatch):
    from fastapi import HTTPException

    from api.routers import academies as router_mod

    listing = router_mod.academies_list()
    ids = {p["program"] for p in listing["programs"]}
    assert {"gaming", "robo", "comms", "analytics", "finance", "rnd"} <= ids

    status = router_mod.academies_status("analytics")
    assert status["program"] == "analytics"
    assert status["total"] == 10

    curriculum = router_mod.academies_curriculum("rnd", level=1)
    assert curriculum["count"] == 5
    assert all(e["level"] == 1 for e in curriculum["exercises"])
    assert curriculum["exercises"][0]["id"] == "RD1.1"

    gate = router_mod.academies_gate("finance")
    assert "gate_open" in gate and "training_only_no_prod_gate" in gate

    with pytest.raises(HTTPException):
        router_mod.academies_status("unknown_program")
