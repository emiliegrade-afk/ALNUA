"""Analytics Drill program config — Hub Autopsy (SPEC_STUDIO_ACADEMIES / DEC-036, Phase 49.4).

Curriculum data lives in ``academy_curriculum_analytics.py``; this module wires
it into an ``AcademyProgram`` for the generic studio_academy engine. QA by
``qa`` (Alex Okafor) — the company-wide QA agent — via the engine's default
DoD review (``run_json_task``). Drill = training only, no production gate.
"""

from __future__ import annotations

from services.academy_curriculum_analytics import LEVEL_META, POLE, SLUG, SUBJECT, all_exercises
from services.studio_academy_program import AcademyProgram

# Local dispatch — analytics room + the QA reviewer.
_AGENT_CLASSES: dict[str, tuple[str, str]] = {
    "analyst_business": ("agents.analyst_business_agent", "BusinessAnalystAgent"),
    "analyst_data": ("agents.analyst_data_agent", "DataAnalystAgent"),
    "qa": ("agents.qa_agent", "QAAgent"),
}

# Methods with a natural free-text param absorbing cross-deliverable context.
_CONTEXT_PARAM: dict[str, str] = {
    "strategic_brief": "context",
    "sql_query": "schema_context",
}

_STUDIO_ROLES = ("analyst_business", "analyst_data")


def _training_only() -> tuple[str, bool]:
    # Drills gate nothing in production — the 5th check just says so.
    return "training_only_no_prod_gate", True


ANALYTICS_PROGRAM = AcademyProgram(
    program_id="analytics",
    title="Hub Autopsy",
    subject=SUBJECT,
    subject_kwarg=None,  # briefs already embed the hub context
    pole=POLE,
    slug=SLUG,
    qa_agent_id="qa",
    agent_classes=_AGENT_CLASSES,
    context_params=_CONTEXT_PARAM,
    level_meta=LEVEL_META,
    progress_env="ANALYTICS_ACADEMY_PROGRESS_PATH",
    progress_filename="analytics_academy_progress.json",
    notes="Analytics Drill — Layla et Axel analysent le Hub lui-même (coûts, activité, académies)",
    runner_module="services.analytics_academy_runner",
    exercises=all_exercises,
    studio_roles=_STUDIO_ROLES,
    gate_n3_check="n3_synthese_complete",
    gate_extra=_training_only,
)
