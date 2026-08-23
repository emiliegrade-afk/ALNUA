"""Tests for Agent Lounge scores — DEC-031 / Phase 46 V2."""

from __future__ import annotations

from pathlib import Path

import pytest

from services import lounge_scores as ls


@pytest.fixture()
def lounge_store(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    path = tmp_path / "lounge_scores.json"
    monkeypatch.setattr(ls, "_SCORES_PATH", path)
    return path


def test_add_lounge_points_and_leaderboard(lounge_store: Path) -> None:
    r = ls.add_lounge_points("dev_app", "session_completed")
    assert r["points_added"] == ls.POINT_VALUES["session_completed"]
    assert r["new_total"] == r["points_added"]
    assert lounge_store.is_file()

    board = ls.get_lounge_leaderboard()
    top = next(row for row in board if row["agent_id"] == "dev_app")
    assert top["score"] == r["new_total"]
    assert top["rank"] >= 1
    assert top["level"] >= 1


def test_lounge_isolated_from_competition(lounge_store: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    from services import competition as comp

    comp_path = lounge_store.parent / "agent_scores.json"
    monkeypatch.setattr(comp, "_SCORES_PATH", comp_path)

    ls.add_lounge_points("dev_app", "duel_won")
    comp.add_points("dev_app", "task_completed")

    assert ls.get_lounge_scores().get("dev_app", 0) == ls.POINT_VALUES["duel_won"]
    assert comp.get_scores().get("dev_app", 0) == comp.POINT_VALUES["task_completed"]
    assert comp_path != lounge_store
    assert not set(ls.get_lounge_scores()).intersection(comp.get_scores()) or (
        ls.get_lounge_scores()["dev_app"] != comp.get_scores()["dev_app"]
    )


def test_archive_month_resets_xp_keeps_badges(lounge_store: Path) -> None:
    # Push past first badge threshold within the month.
    while ls.get_lounge_scores().get("dev_backend", 0) < 100:
        ls.add_lounge_points("dev_backend", "challenge_won")

    profile_before = ls.get_lounge_profile("dev_backend")
    assert "lounge_regular" in profile_before["badges"]
    month = profile_before["month"]

    archived = ls.archive_lounge_month(month)
    assert archived["archived_month"] == month
    assert ls.get_lounge_scores().get("dev_backend", 0) == 0

    profile_after = ls.get_lounge_profile("dev_backend")
    assert "lounge_regular" in profile_after["badges"]
    assert month in ls._load_unlocked()["history"]


def test_custom_points(lounge_store: Path) -> None:
    r = ls.add_lounge_points("qa", "custom", points=7, note="bonus")
    assert r["points_added"] == 7
    assert r["new_total"] == 7
