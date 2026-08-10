"""
rnd_dossier_agent.py — Promote R&D ideas into structured dossiers.

Phase 1: skeleton dossier + sections from idea data.
Phase 2: LLM section drafting, finance, anti-fluff, validate/revise.

Façade : mixins under ``agents/rnd_dossier_*.py`` keep each module ≤ ~300 lines.
"""

from __future__ import annotations

from typing import Any

from agents.agent_base import AgentBase
from agents.rnd_dossier_enrich import RndDossierEnrichMixin
from agents.rnd_dossier_helpers import RndDossierHelpersMixin
from agents.rnd_dossier_llm import RndDossierLlmMixin
from agents.rnd_dossier_workflow import RndDossierWorkflowMixin
from services.rnd_repository import RndRepository, get_rnd_repository


class RndDossierAgent(
    RndDossierWorkflowMixin,
    RndDossierEnrichMixin,
    RndDossierLlmMixin,
    RndDossierHelpersMixin,
    AgentBase,
):
    AGENT_NAME = "rnd_dossier_agent"

    def __init__(self, repo: RndRepository | None = None) -> None:
        super().__init__()
        self.repo = repo or get_rnd_repository()


def promote_idea_to_dossier(
    idea_id: str,
    actor: str = "emilie",
    *,
    enrich: bool = False,
) -> dict[str, Any]:
    return RndDossierAgent().promote_idea(idea_id, actor=actor, enrich=enrich)
