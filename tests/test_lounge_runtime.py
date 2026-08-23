"""Tests Lounge puzzle sessions — Phase 46 V3."""

from __future__ import annotations

from pathlib import Path

import pytest

from services import lounge_runtime as rt
from services import lounge_scores as ls
from services.lounge_activities.puzzle import evaluate_answer, get_puzzle


@pytest.fixture()
def lounge_paths(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(rt, "_SESSIONS_PATH", tmp_path / "lounge_sessions.json")
    monkeypatch.setattr(ls, "_SCORES_PATH", tmp_path / "lounge_scores.json")


def test_evaluate_binary_puzzle() -> None:
    puzzle = get_puzzle("binary-sum")
    assert puzzle is not None
    assert evaluate_answer(puzzle, "16")["won"] is True
    assert evaluate_answer(puzzle, "15")["won"] is False


def test_start_and_complete_awards_xp(lounge_paths: None) -> None:
    session = rt.start_puzzle_session("dev_app", puzzle_id="binary-sum")
    assert session["status"] == "active"
    assert session["puzzle_id"] == "binary-sum"
    assert "correct_answer" not in session

    active = rt.list_active_sessions()
    assert any(s["id"] == session["id"] for s in active)

    done = rt.complete_puzzle_session(session["id"], "16")
    assert done["status"] == "completed"
    assert done["won"] is True
    assert done["score_action"] == "challenge_won"
    assert done["points_awarded"] == ls.POINT_VALUES["challenge_won"]
    assert ls.get_lounge_scores().get("dev_app") == ls.POINT_VALUES["challenge_won"]


def test_wrong_answer_still_session_completed(lounge_paths: None) -> None:
    session = rt.start_puzzle_session("dev_backend", puzzle_id="aluna-acronym")
    done = rt.complete_puzzle_session(session["id"], "bob")
    assert done["won"] is False
    assert done["score_action"] == "session_completed"
    assert ls.get_lounge_scores().get("dev_backend") == ls.POINT_VALUES["session_completed"]


def test_unknown_puzzle_raises(lounge_paths: None) -> None:
    with pytest.raises(ValueError, match="unknown challenge"):
        rt.start_puzzle_session("qa", puzzle_id="does-not-exist")
