"""Comms Academy program config — Lancement NAÏA (SPEC_STUDIO_ACADEMIES / DEC-036).

Curriculum data lives in ``academy_curriculum_comms.py``; this module wires it
into an ``AcademyProgram`` for the generic studio_academy engine.

Side-effect discipline: comms methods that write to production tables (posts
queue, ``campaigns``, dossier assets) are NOT used by the academy. Agents train
via ``handle_instruction`` (marketing, content, ads), the shared AgentBase
``run_json_task`` path (content_* sectors, brand, rnd_social), or a dedicated
paper method (rnd_visual.design_visual_concept). QA by brand (Élise) via the
engine's default DoD review.
"""

from __future__ import annotations

import os

from services.academy_curriculum_comms import LEVEL_META, POLE, SLUG, SUBJECT, all_exercises
from services.studio_academy_program import AcademyProgram

# Local dispatch — comms hub only (same ripple rationale as gaming/robo).
_AGENT_CLASSES: dict[str, tuple[str, str]] = {
    "marketing": ("agents.marketing_agent", "MarketingAgent"),
    "content": ("agents.content_agent", "ContentAgent"),
    "content_app": ("agents.content_app_agent", "ContentAppAgent"),
    "content_gaming": ("agents.content_gaming_agent", "ContentGamingAgent"),
    "content_robo": ("agents.content_robo_agent", "ContentRoboAgent"),
    "content_company": ("agents.content_company_agent", "ContentCompanyAgent"),
    "brand": ("agents.brand_agent", "BrandAgent"),
    "rnd_social": ("agents.rnd_social_agent", "RndSocialAgent"),
    "rnd_visual": ("agents.rnd_visual_agent", "RndVisualAgent"),
    "ads": ("agents.ads_agent", "AdsAgent"),
}

# Where each agent method can absorb cross-deliverable context (N2+ refs).
_CONTEXT_PARAM: dict[str, str] = {
    "design_visual_concept": "context",
}

_STUDIO_ROLES = tuple(_AGENT_CLASSES)


def _v2_prereq() -> tuple[str, bool]:
    # V2 = real activation (posts queued, campaigns created, ad spend) — requires
    # the hub to know which project row NAÏA is.
    return "v2_prereq_naia_project", bool(os.getenv("PROJECT_ID_NAIA", "").strip())


COMMS_PROGRAM = AcademyProgram(
    program_id="comms",
    title="Lancement NAÏA",
    subject=SUBJECT,
    subject_kwarg=None,  # briefs already embed NAÏA context
    pole=POLE,
    slug=SLUG,
    qa_agent_id="brand",
    agent_classes=_AGENT_CLASSES,
    context_params=_CONTEXT_PARAM,
    level_meta=LEVEL_META,
    progress_env="COMMS_ACADEMY_PROGRESS_PATH",
    progress_filename="comms_academy_progress.json",
    notes="Comms Academy — campagne de lancement NAÏA sur papier, avant activation réelle",
    runner_module="services.comms_academy_runner",
    exercises=all_exercises,
    studio_roles=_STUDIO_ROLES,
    gate_n3_check="n3_campaign_complete",
    gate_extra=_v2_prereq,
)
