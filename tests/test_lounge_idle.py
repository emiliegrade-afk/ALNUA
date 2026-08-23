"""Tests Lounge LLM policy + idle lounge_session (Phase 46 V4)."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest


def test_get_lounge_model_empty_uses_tier_fast(monkeypatch: pytest.MonkeyPatch) -> None:
    from config.settings import settings
    from services.lounge_llm import LOUNGE_DEFAULT_MODEL, get_lounge_model

    monkeypatch.setattr(settings, "lounge_model", "")
    assert get_lounge_model() == LOUNGE_DEFAULT_MODEL


def test_get_lounge_model_respects_override(monkeypatch: pytest.MonkeyPatch) -> None:
    from config.settings import settings
    from services.lounge_llm import get_lounge_model

    monkeypatch.setattr(settings, "lounge_model", "openai/gpt-4.1-nano")
    assert get_lounge_model() == "openai/gpt-4.1-nano"


def test_build_day_plan_appends_lounge_filler(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    from services.idle_work_queue import build_day_plan

    monkeypatch.setattr("services.idle_work_queue._QUEUE_PATH", tmp_path / "idle_queue.json")
    q = build_day_plan(autonomy_level=1)
    lounge = [i for i in q["items"] if i.get("kind") == "lounge_session"]
    assert len(lounge) == 1
    assert lounge[0]["level"] == 0
    assert lounge[0]["family"] == "lounge"
    assert q["items"][-1]["kind"] == "lounge_session"


def test_lounge_deferred_on_budget_warning(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    from services.idle_work_queue import build_day_plan, pick_next_item

    monkeypatch.setattr("services.idle_work_queue._QUEUE_PATH", tmp_path / "idle_queue.json")
    build_day_plan(autonomy_level=0)
    with patch(
        "services.idle_work_queue.budget_severity",
        return_value={"severity": "warning"},
    ):
        picked = pick_next_item(max_items=10)
    assert all(i.get("kind") != "lounge_session" for i in picked.get("items") or [])
    assert any(s.get("reason") == "budget_warning_deferred" for s in picked.get("skips") or [])


def test_execute_lounge_session_awards_via_complete(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from services import lounge_runtime as rt
    from services import lounge_scores as ls
    from services.idle_work_recipes import _execute_one

    monkeypatch.setattr(rt, "_SESSIONS_PATH", tmp_path / "lounge_sessions.json")
    monkeypatch.setattr(ls, "_SCORES_PATH", tmp_path / "lounge_scores.json")
    monkeypatch.setattr(
        "services.idle_work_recipes._DELIVERABLES",
        tmp_path / "idle_deliverables",
    )

    def _fake_run(session_id: str) -> dict:
        return rt.complete_session(session_id, "16")

    item = {
        "id": "idle_test_lounge",
        "kind": "lounge_session",
        "agent_id": "dev_app",
        "title": "test",
        "family": "lounge",
        "payload": {"activity": "puzzle", "puzzle_id": "binary-sum"},
    }
    with patch("services.lounge_runtime.run_session_with_llm", side_effect=_fake_run):
        result = _execute_one(item, run_id="run_test")

    assert result["ok"] is True
    assert ls.get_lounge_scores().get("dev_app", 0) > 0
