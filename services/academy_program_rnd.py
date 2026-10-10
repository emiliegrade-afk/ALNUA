"""R&D Drill program config — NUAWAY Next (SPEC_STUDIO_ACADEMIES / DEC-036, Phase 49.4).

Curriculum data lives in ``academy_curriculum_rnd.py``; this module wires it
into an ``AcademyProgram`` for the generic studio_academy engine. All 5 agents
train via ``run_json_task`` (the production R&D pipeline writes to Supabase —
never called here). QA by ``rnd_committee`` (Cléo) via the engine's default
DoD review. Weekly cadence: idle items are only planned on Mondays.
"""

from __future__ import annotations

from services.academy_curriculum_rnd import LEVEL_META, POLE, SLUG, SUBJECT, all_exercises
from services.studio_academy_program import AcademyProgram

# Local dispatch — R&D lab (committee doubles as QA reviewer).
_AGENT_CLASSES: dict[str, tuple[str, str]] = {
    "brainstorm": ("agents.brainstorm_agent", "BrainstormAgent"),
    "rnd_agent": ("agents.rnd_agent", "RndAgent"),
    "rnd_dossier": ("agents.rnd_dossier_agent", "RndDossierAgent"),
    "rnd_ceo": ("agents.rnd_ceo_agent", "RndCeoAgent"),
    "rnd_committee": ("agents.rnd_committee_agent", "RndCommitteeAgent"),
}

# run_json_task absorbs context natively (appended to the prompt).
_CONTEXT_PARAM: dict[str, str] = {}

_STUDIO_ROLES = tuple(_AGENT_CLASSES)


def _training_only() -> tuple[str, bool]:
    return "training_only_no_prod_gate", True


RND_PROGRAM = AcademyProgram(
    program_id="rnd",
    title="NUAWAY Next — dossier papier",
    subject=SUBJECT,
    subject_kwarg=None,
    pole=POLE,
    slug=SLUG,
    qa_agent_id="rnd_committee",
    agent_classes=_AGENT_CLASSES,
    context_params=_CONTEXT_PARAM,
    level_meta=LEVEL_META,
    progress_env="RND_ACADEMY_PROGRESS_PATH",
    progress_filename="rnd_academy_progress.json",
    notes="R&D Drill — dossier exploratoire papier NUAWAY Next, cadence hebdomadaire (lundi)",
    runner_module="services.rnd_academy_runner",
    exercises=all_exercises,
    studio_roles=_STUDIO_ROLES,
    gate_n3_check="n3_verdict_complete",
    gate_extra=_training_only,
)
