"""Analytics Drill runner — Hub Autopsy entry points (SPEC_STUDIO_ACADEMIES / DEC-036, Phase 49.4).

Thin facade over the generic ``studio_academy_engine`` with the analytics
program. Engine defaults used (program dispatch + DoD review via ``QAAgent``'s
AgentBase ``run_json_task``).
"""

from __future__ import annotations

from typing import Any

from services import studio_academy_engine as _engine
from services.academy_program_analytics import ANALYTICS_PROGRAM

__all__ = ["run_exercise", "run_next_exercise", "studio_status"]


def run_exercise(exercise_id: str, *, qa_enabled: bool = True) -> dict[str, Any]:
    return _engine.run_exercise(ANALYTICS_PROGRAM, exercise_id, qa_enabled=qa_enabled)


def run_next_exercise(*, qa_enabled: bool = True) -> dict[str, Any]:
    return _engine.run_next_exercise(ANALYTICS_PROGRAM, qa_enabled=qa_enabled)


def studio_status() -> dict[str, Any]:
    return _engine.studio_status(ANALYTICS_PROGRAM)
