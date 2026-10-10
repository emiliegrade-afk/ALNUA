"""Robo Academy runner — Eve Paper Build entry points (SPEC_STUDIO_ACADEMIES / DEC-036).

Thin facade over the generic ``studio_academy_engine`` with the robo program.
No custom dispatch/QA hooks: the engine defaults (program dispatch + DoD review
via ``QaRobotAgent.run_json_task``) are used.
"""

from __future__ import annotations

from typing import Any

from services import studio_academy_engine as _engine
from services.academy_program_robo import ROBO_PROGRAM

__all__ = ["run_exercise", "run_next_exercise", "studio_status"]


def run_exercise(exercise_id: str, *, qa_enabled: bool = True) -> dict[str, Any]:
    return _engine.run_exercise(ROBO_PROGRAM, exercise_id, qa_enabled=qa_enabled)


def run_next_exercise(*, qa_enabled: bool = True) -> dict[str, Any]:
    return _engine.run_next_exercise(ROBO_PROGRAM, qa_enabled=qa_enabled)


def studio_status() -> dict[str, Any]:
    return _engine.studio_status(ROBO_PROGRAM)
