"""Tests Lounge V6 — multi-activity + tournaments."""

from __future__ import annotations

from pathlib import Path

import pytest

from services import lounge_runtime as rt
from services import lounge_scores as ls
from services import lounge_tournaments as lt
from services.lounge_activities.catalog import (
    ACTIVITY_IDS,
    evaluate_challenge,
    list_activities,
    pick_challenge,
)


@pytest.fixture()
def lounge_paths(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(rt, "_SESSIONS_PATH", tmp_path / "lounge_sessions.json")
    monkeypatch.setattr(ls, "_SCORES_PATH", tmp_path / "lounge_scores.json")
    monkeypatch.setattr(lt, "_PATH", tmp_path / "lounge_tournaments.json")


def test_all_activities_live() -> None:
    rows = list_activities()
    assert len(rows) == 7
    assert {r["id"] for r in rows} == set(ACTIVITY_IDS)
    assert all(r["status"] == "live" and r["challenge_count"] >= 1 for r in rows)


def test_arcade_exact_win(lounge_paths: None) -> None:
    session = rt.start_session("dev_app", "arcade", "arcade-seq-3")
    assert session["activity"] == "arcade"
    done = rt.complete_session(session["id"], "9")
    assert done["won"] is True
    assert done["score_action"] == "challenge_won"


def test_code_challenge_exact(lounge_paths: None) -> None:
    ch = pick_challenge("code_challenge")
    result = evaluate_challenge(ch, ch["answer"])
    assert result["won"] is True


def test_llm_free_min_chars() -> None:
    ch = pick_challenge("creative", "creative-tagline")
    assert ch["mode"] == "llm_free"
    short = evaluate_challenge(ch, "trop court")
    assert short["won"] is False
    long = evaluate_challenge(ch, "x" * 45)
    assert long["won"] is True


def test_tournaments_seeded(lounge_paths: None) -> None:
    events = lt.list_tournaments()
    assert len(events) >= 4
    assert all("title" in e and "when_label" in e for e in events)


def test_start_session_unknown_challenge(lounge_paths: None) -> None:
    with pytest.raises(ValueError, match="unknown challenge"):
        rt.start_session("qa", "puzzle", "does-not-exist")
