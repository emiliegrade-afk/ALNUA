"""Context Engine L1–L4 + collective promotion — Phase F (DEC-027)."""

from __future__ import annotations

import pytest

from services.collective_learning import (
    lesson_fingerprint,
    list_collective_lessons,
    record_lesson_candidate,
)
from services.context_engine import compile_context
from services.working_memory import (
    get_working_memory,
    set_working_memory,
    wipe_working_memory,
)


@pytest.fixture
def mem_paths(tmp_path, monkeypatch: pytest.MonkeyPatch):
    wm = tmp_path / "working_memory"
    wm.mkdir()
    monkeypatch.setattr("services.working_memory._DIR", wm)
    monkeypatch.setattr(
        "services.collective_learning._CANDIDATES",
        tmp_path / "lesson_candidates.json",
    )
    monkeypatch.setattr(
        "services.collective_learning._COLLECTIVE",
        tmp_path / "collective_lessons.json",
    )
    monkeypatch.setenv("CONTEXT_ENGINE_ENABLED", "1")
    monkeypatch.setenv("COLLECTIVE_PROMOTE_MIN_AGENTS", "3")
    try:
        from config.settings import get_settings

        get_settings.cache_clear()
    except Exception:
        pass
    return tmp_path


def test_compile_has_l1_and_optional_l4(mem_paths, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "skills.skill_agent_learning_context.get_learning_context",
        lambda *_a, **_k: "\n\n─── LEÇONS ───\nfake l3\n",
    )
    monkeypatch.setattr(
        "skills.skill_agent_learning_context.get_library_context",
        lambda *_a, **_k: "",
    )
    monkeypatch.setattr(
        "config.agent_personas.get_room",
        lambda aid: "app_office",
    )
    bundle = compile_context(
        "dev_app",
        "implement feature",
        task_id="plan:1",
        loop_feedback="tests failed: assert x",
        include_library=False,
    )
    block = bundle.as_block()
    assert "L1 POLICIES" in block
    assert "L2 STANDARDS" in block
    assert "L4 WORKING" in block
    assert "tests failed" in block
    assert bundle.l3  # mocked


def test_wipe_l4(mem_paths) -> None:
    set_working_memory("t1", agent_id="qa", feedback="boom")
    assert get_working_memory("t1") is not None
    assert wipe_working_memory("t1") is True
    assert get_working_memory("t1") is None


def test_loop_engine_wipes_l4(mem_paths) -> None:
    from services.loop_engine import EvalVerdict, LoopContext, run_loop

    def execute(ctx: LoopContext) -> str:
        return "x"

    def evaluate(value: str, ctx: LoopContext) -> EvalVerdict:
        if ctx.iteration < 2:
            return EvalVerdict(approved=False, feedback="retry once")
        return EvalVerdict(approved=True)

    result = run_loop(
        execute=execute,
        evaluate=evaluate,
        max_iterations=3,
        loop_id="loop-wipe-1",
        sleep_s=0,
    )
    assert result.success
    assert get_working_memory("loop-wipe-1") is None


def test_collective_promotion(mem_paths, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "services.collective_learning._room_for",
        lambda aid: "app_office",
    )
    lesson = "Toujours lancer pytest avant d'ouvrir la PR staging."
    assert lesson_fingerprint(lesson) == lesson_fingerprint(lesson.upper())

    r1 = record_lesson_candidate("dev_app", lesson, task="a")
    r2 = record_lesson_candidate("dev_backend", lesson, task="b")
    assert r1["promoted"] is False
    assert r2["promoted"] is False
    r3 = record_lesson_candidate("dev_frontend", lesson, task="c")
    assert r3["promoted"] is True
    rows = list_collective_lessons(room="app_office")
    assert len(rows) >= 1
    assert "pytest" in rows[0]["lesson"].lower()


def test_inject_uses_context_engine(mem_paths, monkeypatch: pytest.MonkeyPatch) -> None:
    from skills.skill_agent_learning_context import inject_learning_context

    monkeypatch.setattr(
        "skills.skill_agent_learning_context.get_learning_context",
        lambda *_a, **_k: "",
    )
    monkeypatch.setattr(
        "skills.skill_agent_learning_context.get_library_context",
        lambda *_a, **_k: "",
    )
    monkeypatch.setattr("config.agent_personas.get_room", lambda aid: "direction")
    out = inject_learning_context("PROMPT", "coo", "plan day", task_id=None)
    assert out.startswith("PROMPT")
    assert "L1 POLICIES" in out


def test_context_api(hub_client, mem_paths) -> None:
    from tests.conftest import HUB_HEADERS

    d = hub_client.get("/context/defaults", headers=HUB_HEADERS)
    assert d.status_code == 200
    assert d.json()["layers"] == ["L1", "L2", "L3", "L4"]

    c = hub_client.post(
        "/context/compile",
        headers=HUB_HEADERS,
        json={
            "agent_id": "qa",
            "task": "review diff",
            "loop_feedback": "spec rejected: naming",
            "include_library": False,
        },
    )
    assert c.status_code == 200
    body = c.json()
    assert body["layers"]["l1"] is True
    assert "L1" in body["preview"]

    w = hub_client.post(
        "/context/working-memory",
        headers=HUB_HEADERS,
        json={"task_id": "api-t1", "agent_id": "qa", "feedback": "retry me"},
    )
    assert w.status_code == 200
    wipe = hub_client.delete("/context/working-memory/api-t1", headers=HUB_HEADERS)
    assert wipe.status_code == 200
    assert wipe.json()["wiped"] is True
