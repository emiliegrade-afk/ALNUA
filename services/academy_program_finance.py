"""Finance Drill program config — Budgets Projets Papier (SPEC_STUDIO_ACADEMIES / DEC-036, Phase 49.4).

Curriculum data lives in ``academy_curriculum_finance.py``; this module wires
it into an ``AcademyProgram`` for the generic studio_academy engine. All
methods used are read-only (no ledger writes). QA by ``qa`` (Alex Okafor) via
the engine's default DoD review. Drill = training only, no production gate.
"""

from __future__ import annotations

from services.academy_curriculum_finance import LEVEL_META, POLE, SLUG, SUBJECT, all_exercises
from services.studio_academy_program import AcademyProgram

# Local dispatch — accounting office + the QA reviewer.
_AGENT_CLASSES: dict[str, tuple[str, str]] = {
    "accounting": ("agents.accountant_agent", "AccountantAgent"),
    "controller": ("agents.controller_agent", "ControllerAgent"),
    "qa": ("agents.qa_agent", "QAAgent"),
}

# No explicit map: kwarg order in the curriculum puts a free-text param last
# (engine fallback for cross-deliverable context).
_CONTEXT_PARAM: dict[str, str] = {}

_STUDIO_ROLES = ("accounting", "controller")


def _training_only() -> tuple[str, bool]:
    return "training_only_no_prod_gate", True


FINANCE_PROGRAM = AcademyProgram(
    program_id="finance",
    title="Budgets Projets Papier",
    subject=SUBJECT,
    subject_kwarg=None,
    pole=POLE,
    slug=SLUG,
    qa_agent_id="qa",
    agent_classes=_AGENT_CLASSES,
    context_params=_CONTEXT_PARAM,
    level_meta=LEVEL_META,
    progress_env="FINANCE_ACADEMY_PROGRESS_PATH",
    progress_filename="finance_academy_progress.json",
    notes="Finance Drill — Jules et Rémi budgètent les projets papier (Eve, NAÏA, Hub)",
    runner_module="services.finance_academy_runner",
    exercises=all_exercises,
    studio_roles=_STUDIO_ROLES,
    gate_n3_check="n3_arbitrage_complete",
    gate_extra=_training_only,
)
