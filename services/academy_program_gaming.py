"""Gaming Academy program config — generic engine glue (DEC-036).

Curriculum data lives in ``academy_curriculum_gaming.py``; this module only
wires it into an ``AcademyProgram`` consumed by the studio_academy engine.
"""

from __future__ import annotations

import os

from services.academy_curriculum_gaming import GAME, LEVEL_META, POLE, SLUG, all_exercises
from services.studio_academy_program import AcademyProgram

# Local dispatch — gaming studio only. Kept out of agent_pipeline_registry on
# purpose: that registry serves plan_executor/parallel_runner (ripple risk).
_AGENT_CLASSES: dict[str, tuple[str, str]] = {
    "game_director": ("agents.game_director_agent", "GameDirectorAgent"),
    "dev_gaming": ("agents.dev_gaming_agent", "DevGamingAgent"),
    "narrative_designer": ("agents.narrative_designer_agent", "NarrativeDesignerAgent"),
    "level_designer": ("agents.level_designer_agent", "LevelDesignerAgent"),
    "environment_artist": ("agents.environment_artist_agent", "EnvironmentArtistAgent"),
    "technical_artist": ("agents.technical_artist_agent", "TechnicalArtistAgent"),
    "vfx_artist": ("agents.vfx_artist_agent", "VfxArtistAgent"),
    "sound_designer": ("agents.sound_designer_agent", "SoundDesignerAgent"),
    "ai_programmer": ("agents.ai_programmer_agent", "AiProgrammerAgent"),
    "qa_gaming": ("agents.qa_gaming_agent", "QaGamingAgent"),
}

# Where each agent method can absorb cross-deliverable context (N2+ refs).
_CONTEXT_PARAM: dict[str, str] = {
    "design_quest": "lore_context",
    "write_dialogue": "context",
    "build_test_plan": "risk_areas",
    "optimize_render_budget": "current_issues",
    "design_level": "special_mechanics",
}

_STUDIO_ROLES = tuple(_AGENT_CLASSES)


def _v2_prereq() -> tuple[str, bool]:
    repo = os.getenv("GITHUB_REPO_GAMING", "").strip()
    path = os.getenv("UE_PROJECT_PATH", "").strip() or os.getenv("REPO_PATH_GAMING", "").strip()
    return "v2_prereq_configured", bool(repo and path)


GAMING_PROGRAM = AcademyProgram(
    program_id="gaming",
    title="Wyrdheim Paper Slice",
    subject=GAME,
    subject_kwarg="game",
    pole=POLE,
    slug=SLUG,
    qa_agent_id="qa_gaming",
    agent_classes=_AGENT_CLASSES,
    context_params=_CONTEXT_PARAM,
    level_meta=LEVEL_META,
    progress_env="GAMING_ACADEMY_PROGRESS_PATH",
    progress_filename="gaming_academy_progress.json",
    notes="Gaming Academy — Wyrdheim Paper Slice, formation studio avant production UE5.8",
    runner_module="services.gaming_academy_runner",
    exercises=all_exercises,
    studio_roles=_STUDIO_ROLES,
    gate_n3_check="n3_slice_complete",
    gate_extra=_v2_prereq,
)
