"""Tests ALNUA Academy — Phase 2."""

from __future__ import annotations

from services.academy_curriculum import (
    LEVEL_META,
    all_exercises,
    exercise_by_id,
    exercises_for_level,
)


def test_curriculum_has_52_exercises() -> None:
    exercises = all_exercises()
    assert len(exercises) == 52
    assert sum(LEVEL_META[lv]["issues"] for lv in LEVEL_META) == 52


def test_level_counts() -> None:
    assert len(exercises_for_level(1)) == 10
    assert len(exercises_for_level(2)) == 12
    assert len(exercises_for_level(3)) == 10
    assert len(exercises_for_level(4)) == 20


def test_exercise_ids_unique() -> None:
    ids = [e.exercise_id for e in all_exercises()]
    assert len(ids) == len(set(ids))


def test_issue_body_has_stack() -> None:
    ex = exercise_by_id("N1.1")
    assert ex is not None
    body = ex.issue_body()
    assert "## Stack" in body
    assert "react_native_expo" in body


def test_github_title_prefix() -> None:
    ex = exercise_by_id("N2.5")
    assert ex is not None
    assert ex.github_title().startswith("[ACADEMY N2.5]")


def test_default_progress_structure() -> None:
    from services.academy_progress import default_progress

    p = default_progress()
    assert p["total_exercises"] == 52
    assert "gate_academy" in p
    assert p["levels"]["1"]["total"] == 10
