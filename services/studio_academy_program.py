"""Studio Academy — program registry (SPEC_STUDIO_ACADEMIES / DEC-036).

One ``AcademyProgram`` per department (gaming, robo, comms…). The generic
engine (``studio_academy_state`` / ``studio_academy_engine`` /
``studio_academy_gate``) is parameterized by these configs — no per-department
copies of runner/progress/gate logic.
"""

from __future__ import annotations

import os
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path

_PROJECT_ROOT = Path(__file__).resolve().parent.parent


@dataclass(frozen=True)
class StudioExercise:
    exercise_id: str
    level: int
    agent_id: str
    method: str
    title: str
    brief: str
    deliverable_path: str  # relative to workspace pole dir, e.g. "meca/chassis-principal.md"
    method_kwargs: dict[str, str] = field(default_factory=dict)
    context_refs: list[str] = field(default_factory=list)  # deliverable paths of earlier exercises
    dod: list[str] = field(default_factory=list)


def exercise_sort_key(ex: StudioExercise) -> tuple[int, ...]:
    """Numeric order: RN1.10 must come after RN1.2 (string sort gets it wrong)."""
    return tuple(int(p) for p in ex.exercise_id[2:].split("."))


@dataclass(frozen=True)
class AcademyProgram:
    program_id: str  # "gaming" | "robo"
    title: str  # "Wyrdheim Paper Slice"
    subject: str  # project name used in prompts/status ("Wyrdheim", "Eve")
    subject_kwarg: str | None  # method kwarg receiving the subject ("game"), None if none
    pole: str  # workspace pole (rnd_workspace.WORKSPACE_POLES)
    slug: str  # workspace slug
    qa_agent_id: str
    agent_classes: dict[str, tuple[str, str]]  # agent_id → (module, class)
    context_params: dict[str, str]  # method → kwarg absorbing cross-deliverable context
    level_meta: dict[int, dict[str, str | int]]
    progress_env: str  # env var overriding the progress file path
    progress_filename: str  # default location: data/<progress_filename>
    notes: str  # default_progress "notes" field
    runner_module: str  # module exposing run_next_exercise/run_exercise/studio_status
    exercises: Callable[[], list[StudioExercise]]
    studio_roles: tuple[str, ...]
    gate_n3_check: str  # check name for "level 3 fully validated"
    gate_extra: Callable[[], tuple[str, bool]]  # program-specific 5th gate check

    def progress_path(self) -> Path:
        return Path(os.getenv(self.progress_env, str(_PROJECT_ROOT / "data" / self.progress_filename)))


_PROGRAMS: dict[str, AcademyProgram] = {}


def get_program(program_id: str) -> AcademyProgram:
    if not _PROGRAMS:
        _bootstrap()
    try:
        return _PROGRAMS[program_id]
    except KeyError:
        raise KeyError(f"unknown academy program: {program_id}") from None


def all_programs() -> list[AcademyProgram]:
    if not _PROGRAMS:
        _bootstrap()
    return list(_PROGRAMS.values())


def _bootstrap() -> None:
    """Lazy import: program modules import dataclasses from here (no cycle)."""
    from services.academy_program_analytics import ANALYTICS_PROGRAM
    from services.academy_program_comms import COMMS_PROGRAM
    from services.academy_program_finance import FINANCE_PROGRAM
    from services.academy_program_gaming import GAMING_PROGRAM
    from services.academy_program_rnd import RND_PROGRAM
    from services.academy_program_robo import ROBO_PROGRAM

    for program in (GAMING_PROGRAM, ROBO_PROGRAM, COMMS_PROGRAM, ANALYTICS_PROGRAM, FINANCE_PROGRAM, RND_PROGRAM):
        _PROGRAMS[program.program_id] = program
