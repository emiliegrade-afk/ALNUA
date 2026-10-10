"""Gaming Academy runner — compat wrapper (DEC-036).

Logic lives in the generic ``studio_academy_engine``; this module keeps the
historical API plus the ``_get_agent``/``_qa_review`` hooks (read at call time
so tests can monkeypatch dispatch). Gaming keeps its dedicated QA method
``QaGamingAgent.review_deliverable`` — proven in production.
"""

from __future__ import annotations

import importlib
from typing import Any

from services import studio_academy_engine as _engine
from services.academy_program_gaming import _AGENT_CLASSES, GAMING_PROGRAM
from services.academy_program_gaming import _CONTEXT_PARAM as _CONTEXT_PARAM  # compat re-export

__all__ = ["run_exercise", "run_next_exercise", "studio_status"]


def _get_agent(agent_id: str) -> Any:
    module_name, class_name = _AGENT_CLASSES[agent_id]
    cls = getattr(importlib.import_module(module_name), class_name)
    return cls()


def _qa_review(exercise: Any, content: str) -> dict[str, Any]:
    qa = _get_agent("qa_gaming")
    return qa.review_deliverable(exercise.title, content, exercise.dod)


def run_exercise(exercise_id: str, *, qa_enabled: bool = True) -> dict[str, Any]:
    return _engine.run_exercise(
        GAMING_PROGRAM, exercise_id, qa_enabled=qa_enabled, get_agent=_get_agent, qa_review=_qa_review
    )


def run_next_exercise(*, qa_enabled: bool = True) -> dict[str, Any]:
    return _engine.run_next_exercise(
        GAMING_PROGRAM, qa_enabled=qa_enabled, get_agent=_get_agent, qa_review=_qa_review
    )


def studio_status() -> dict[str, Any]:
    return _engine.studio_status(GAMING_PROGRAM)
