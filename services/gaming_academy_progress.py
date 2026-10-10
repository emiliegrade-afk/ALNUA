"""Gaming Academy progress — compat wrapper (DEC-036).

Logic lives in the generic ``studio_academy_state`` engine; this module keeps
the historical API and the ``_PROGRESS_PATH`` module attribute (read at call
time so tests can monkeypatch it).
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from services import studio_academy_state as _state
from services.studio_academy_program import get_program

_PROJECT_ROOT = Path(__file__).resolve().parent.parent
_PROGRESS_PATH = Path(
    os.getenv(
        "GAMING_ACADEMY_PROGRESS_PATH",
        str(_PROJECT_ROOT / "data" / "gaming_academy_progress.json"),
    )
)

MAX_QA_ATTEMPTS = _state.MAX_QA_ATTEMPTS


def _program():
    return get_program("gaming")


def default_progress() -> dict[str, Any]:
    return _state.default_progress(_program())


def load_progress() -> dict[str, Any]:
    return _state.load_progress(_program(), _PROGRESS_PATH)


def save_progress(data: dict[str, Any]) -> Path:
    return _state.save_progress(_program(), data, _PROGRESS_PATH)


def record_exercise_result(exercise_id: str, **kwargs: Any) -> dict[str, Any]:
    return _state.record_exercise_result(_program(), exercise_id, progress_path=_PROGRESS_PATH, **kwargs)


def next_pending_exercise() -> Any | None:
    return _state.next_pending_exercise(_program(), _PROGRESS_PATH)
