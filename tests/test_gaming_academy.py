"""Tests for the Gaming Academy (SPEC_GAMING_ACADEMY / DEC-034).

No LLM calls: agent dispatch and QA review are monkeypatched. Workspace writes
are redirected to a tmp dir via ALNUA_WORKSPACE, progress via
GAMING_ACADEMY_PROGRESS_PATH.
"""

from __future__ import annotations

import pytest

from services import gaming_academy_progress as progress_mod
from services import gaming_academy_runner as runner_mod
from services.gaming_academy_curriculum import LEVEL_META, all_exercises, get_exercise
from services.gaming_academy_gate import evaluate_gate


@pytest.fixture(autouse=True)
def isolated_state(tmp_path, monkeypatch):
    monkeypatch.setenv("ALNUA_WORKSPACE", str(tmp_path / "ws"))
    monkeypatch.setenv("GAMING_ACADEMY_PROGRESS_PATH", str(tmp_path / "progress.json"))
    monkeypatch.setattr(progress_mod, "_PROGRESS_PATH", tmp_path / "progress.json")
    return tmp_path


# ---------------------------------------------------------------------------
# Curriculum integrity
# ---------------------------------------------------------------------------


def test_curriculum_has_30_unique_exercises():
    exercises = all_exercises()
    assert len(exercises) == 30
    ids = [e.exercise_id for e in exercises]
    assert len(set(ids)) == 30
    paths = [e.deliverable_path for e in exercises]
    assert len(set(paths)) == 30


def test_curriculum_levels_match_meta():
    counts: dict[int, int] = {}
    for ex in all_exercises():
        assert 1 <= ex.level <= 4
        counts[ex.level] = counts.get(ex.level, 0) + 1
    for lv, meta in LEVEL_META.items():
        assert counts.get(lv, 0) == int(meta["exercises"]), f"level {lv} count mismatch"


def test_curriculum_all_studio_roles_covered():
    agents = {e.agent_id for e in all_exercises()}
    assert agents == set(runner_mod._AGENT_CLASSES)


def test_curriculum_exercises_have_dod_and_known_agent():
    for ex in all_exercises():
        assert ex.dod, f"{ex.exercise_id} missing DoD"
        assert ex.agent_id in runner_mod._AGENT_CLASSES, f"{ex.exercise_id} unknown agent"
        assert ex.method, f"{ex.exercise_id} missing method"


def test_curriculum_refs_point_to_earlier_exercises():
    seen: set[str] = set()
    from services.gaming_academy_curriculum import exercise_sort_key

    for ex in sorted(all_exercises(), key=exercise_sort_key):
        for ref in ex.context_refs:
            assert ref in seen, f"{ex.exercise_id} refs {ref} before it is produced"
        seen.add(ex.deliverable_path)


def test_get_exercise_lookup():
    assert get_exercise("GN1.3").agent_id == "level_designer"
    assert get_exercise("GN9.9") is None


# ---------------------------------------------------------------------------
# Progress
# ---------------------------------------------------------------------------


def test_progress_default_and_record_cycle():
    data = progress_mod.load_progress()
    assert data["total_exercises"] == 30
    assert data["current_level"] == 1

    progress_mod.record_exercise_result("GN1.3", status="in_progress")
    progress_mod.record_exercise_result("GN1.3", status="validated", qa_verdict="validated", path="quests/x.md")
    data = progress_mod.load_progress()
    assert data["exercises"]["GN1.3"]["status"] == "validated"
    assert data["completed_exercises"] == 1
    assert data["success_rate_pct"] == 100.0
    assert data["levels"]["1"]["done"] == 1


def test_progress_next_pending_skips_terminal():
    progress_mod.record_exercise_result("GN1.1", status="validated")
    nxt = progress_mod.next_pending_exercise()
    assert nxt is not None and nxt.exercise_id == "GN1.2"


def test_progress_failed_after_max_attempts_is_terminal():
    for _ in range(progress_mod.MAX_QA_ATTEMPTS):
        progress_mod.record_exercise_result("GN1.1", status="in_progress")
        progress_mod.record_exercise_result("GN1.1", status="failed")
    ids = {e.exercise_id for e in all_exercises()} - {"GN1.1"}
    nxt = progress_mod.next_pending_exercise()
    assert nxt.exercise_id in ids


# ---------------------------------------------------------------------------
# Runner (mocked agent + QA)
# ---------------------------------------------------------------------------


class _FakeAgent:
    """Answers any agent method with a minimal valid payload."""

    def __getattr__(self, name: str):
        def _fake(**kwargs):
            return {"method": name, "summary": "livrable factice", "items": ["a", "b", "c"]}

        return _fake

    def design_quest(self, **kwargs):
        assert kwargs["quest_name"] == "Premiers Pas"
        assert kwargs["game"] == "Wyrdheim"
        return {
            "quest_id": "premiers_pas",
            "title": "Premiers Pas",
            "objectives": [{"id": 1, "description": "Marcher", "type": "explore"}],
            "rewards": {"xp": 50},
        }


def _patch_dispatch(monkeypatch, qa_verdict="validated"):
    monkeypatch.setattr(runner_mod, "_get_agent", lambda agent_id: _FakeAgent())
    monkeypatch.setattr(
        runner_mod,
        "_qa_review",
        lambda ex, content: {"verdict": qa_verdict, "dod_checks": [], "feedback": "ok" if qa_verdict == "validated" else "trop vague"},
    )


def test_run_exercise_end_to_end_validated(monkeypatch):
    _patch_dispatch(monkeypatch)
    result = runner_mod.run_exercise("GN1.3")
    assert result["ok"] is True
    assert result["status"] == "validated"
    assert result["path"] == "quests/quete-tutoriel-01.md"

    from services.rnd_workspace import read_deliverable

    content = read_deliverable("gaming", "gaming-academy", result["path"])
    assert "Premiers Pas" in content
    assert "quest_id" in content

    data = progress_mod.load_progress()
    assert data["exercises"]["GN1.3"]["status"] == "validated"


def test_run_exercise_qa_rejection_then_retry_versioned(monkeypatch):
    _patch_dispatch(monkeypatch, qa_verdict="rejected")
    first = runner_mod.run_exercise("GN1.3")
    assert first["status"] == "rejected"

    _patch_dispatch(monkeypatch, qa_verdict="validated")
    second = runner_mod.run_exercise("GN1.3")
    assert second["status"] == "validated"
    assert second["path"] == "quests/quete-tutoriel-01-v2.md"  # write-only, no overwrite


def test_run_exercise_skips_terminal(monkeypatch):
    _patch_dispatch(monkeypatch)
    runner_mod.run_exercise("GN1.3")
    again = runner_mod.run_exercise("GN1.3")
    assert again.get("skipped") is True


def test_run_exercise_unknown_id():
    assert runner_mod.run_exercise("GN9.9")["ok"] is False


def test_run_next_exercise_picks_first_pending(monkeypatch):
    _patch_dispatch(monkeypatch)
    result = runner_mod.run_next_exercise()
    assert result["ok"] is True
    assert result["exercise_id"] == "GN1.1"
    assert result["status"] == "validated"


# ---------------------------------------------------------------------------
# Gate
# ---------------------------------------------------------------------------


def test_gate_empty_progress_blocks():
    gate = evaluate_gate()
    assert gate["gate_open"] is False
    assert gate["readiness_pct"] == 0.0
    assert gate["success_rate_65"] is False


def test_gate_full_success_opens_with_v2_prereq(monkeypatch):
    monkeypatch.setenv("GITHUB_REPO_GAMING", "alnua-org/wyrdheim")
    monkeypatch.setenv("UE_PROJECT_PATH", "D:/Dev/wyrdheim")
    for ex in all_exercises():
        progress_mod.record_exercise_result(ex.exercise_id, status="validated")
    gate = evaluate_gate()
    assert gate["success_rate_65"] is True
    assert gate["n3_slice_complete"] is True
    assert gate["roles_coverage_10"] is True
    assert gate["canon_clean"] is True
    assert gate["v2_prereq_configured"] is True
    assert gate["gate_open"] is True
    assert gate["readiness_pct"] == 100.0


def test_gate_canon_conflict_blocks(monkeypatch):
    monkeypatch.setenv("GITHUB_REPO_GAMING", "alnua-org/wyrdheim")
    monkeypatch.setenv("UE_PROJECT_PATH", "D:/Dev/wyrdheim")
    for ex in all_exercises():
        progress_mod.record_exercise_result(ex.exercise_id, status="validated")
    progress_mod.record_exercise_result("GN2.1", status="rejected", canon_conflict=True)
    gate = evaluate_gate()
    assert gate["canon_clean"] is False
    assert gate["gate_open"] is False


# ---------------------------------------------------------------------------
# 48.2 — Idle integration + endpoints
# ---------------------------------------------------------------------------


def test_day_plan_includes_gaming_academy_items(tmp_path, monkeypatch):
    monkeypatch.setattr("services.idle_work_queue._QUEUE_PATH", tmp_path / "idle_queue.json")
    from services.idle_work_queue import build_day_plan

    queue = build_day_plan(autonomy_level=1)
    gaming = [i for i in queue["items"] if i["kind"] == "gaming_academy_exercise"]
    assert len(gaming) == 2
    for item in gaming:
        assert item["level"] == 1
        assert item["family"] == "gaming"
        assert item["status"] == "pending"


def test_day_plan_autonomy_l0_excludes_gaming(tmp_path, monkeypatch):
    monkeypatch.setattr("services.idle_work_queue._QUEUE_PATH", tmp_path / "idle_queue.json")
    from services.idle_work_queue import build_day_plan

    queue = build_day_plan(autonomy_level=0)
    assert not [i for i in queue["items"] if i["kind"] == "gaming_academy_exercise"]


def test_gaming_item_deferred_on_budget_warning():
    from services.idle_work_queue import _item_eligible

    item = {"status": "pending", "level": 1, "kind": "gaming_academy_exercise", "family": "gaming"}
    assert _item_eligible(item, {}, "warning") == "budget_warning_deferred"
    assert _item_eligible(item, {}, "ok") is None


def test_recipe_executes_gaming_academy_kind(tmp_path, monkeypatch):
    monkeypatch.setattr("services.idle_work_recipes._DELIVERABLES", tmp_path / "deliv")
    marked: list[dict] = []
    monkeypatch.setattr("services.idle_work_queue.mark_item", lambda *a, **kw: marked.append(kw))
    monkeypatch.setattr(
        runner_mod,
        "run_next_exercise",
        lambda: {"ok": True, "exercise_id": "GN1.2", "status": "validated", "path": "narrative/x.md"},
    )
    from services.idle_work_recipes import _execute_one

    result = _execute_one(
        {"id": "idle_test1", "kind": "gaming_academy_exercise", "agent_id": "game_director", "title": "t"},
        "run-1",
    )
    assert result["ok"] is True
    assert "GN1.2" in result["detail"]
    assert marked and marked[0]["status"] == "done"


def test_recipe_gaming_academy_nothing_pending_is_done(tmp_path, monkeypatch):
    monkeypatch.setattr("services.idle_work_recipes._DELIVERABLES", tmp_path / "deliv")
    monkeypatch.setattr("services.idle_work_queue.mark_item", lambda *a, **kw: None)
    monkeypatch.setattr(runner_mod, "run_next_exercise", lambda: {"ok": True, "reason": "nothing_pending"})
    from services.idle_work_recipes import _execute_one

    result = _execute_one(
        {"id": "idle_test2", "kind": "gaming_academy_exercise", "agent_id": "game_director", "title": "t"},
        None,
    )
    assert result["ok"] is True
    assert "nothing_pending" in result["detail"]


def test_router_endpoints(monkeypatch):
    from api.routers import gaming_academy as router_mod_ga

    monkeypatch.setattr(runner_mod, "studio_status", lambda: {"game": "Wyrdheim", "completed": 1})
    assert router_mod_ga.gaming_academy_status()["game"] == "Wyrdheim"

    monkeypatch.setattr(runner_mod, "run_exercise", lambda eid: {"ok": True, "exercise_id": eid})
    assert router_mod_ga.gaming_academy_run("GN1.3")["exercise_id"] == "GN1.3"

    curriculum = router_mod_ga.gaming_academy_curriculum(level=1)
    assert curriculum["count"] == 10
    assert all(e["level"] == 1 for e in curriculum["exercises"])
    assert curriculum["exercises"][0]["id"] == "GN1.1"  # numeric sort, not lexicographic

    gate = router_mod_ga.gaming_academy_gate()
    assert "gate_open" in gate and "readiness_pct" in gate
