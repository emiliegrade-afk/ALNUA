"""
rnd_social_agent.py — Social teaser pipeline for R&D dossiers (phase 5).

Calendar → posts_queue with rnd_dossier_id / rnd_social_calendar_id links.
Façade : mixins under ``agents/rnd_social_*.py`` keep each module ≤ ~300 lines.
"""

from __future__ import annotations

from agents.agent_base import AgentBase
from agents.rnd_social_calendar import RndSocialCalendarMixin
from agents.rnd_social_helpers import (  # noqa: F401 — public API re-export
    _template_post,
    ensure_project_for_dossier,
    resolve_project_for_dossier,
)
from agents.rnd_social_posts import RndSocialPostsMixin
from services.rnd_repository import get_rnd_repository
from services.rnd_social import get_rnd_social_repository


class RndSocialAgent(
    RndSocialPostsMixin,
    RndSocialCalendarMixin,
    AgentBase,
):
    AGENT_NAME = "rnd_social_agent"

    def __init__(self) -> None:
        super().__init__()
        self.repo = get_rnd_repository()
        self.social = get_rnd_social_repository()
