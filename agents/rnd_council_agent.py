"""
rnd_council_agent.py — Conseil stratégique R&D (Phase 25, ROADMAP.md).

Débat multi-agents SANS dossier obligatoire (idéation pure ou évaluation
structurée) — contrairement à `RndCommitteeAgent` (agents/rnd_committee_agent.py)
qui exige toujours un `dossier_id` réel. Nouvelle orchestration légère, pas
une sous-classe : `RndCommitteeAgent` n'est ni touché ni étendu.

Les 5 membres du Conseil sont des personas dédiées au Conseil uniquement —
pas des agents/*.py individuels (ils n'ont pas de méthode solo, seulement une
participation aux délibérations), donc pas d'entrée dans
config/agent_personas.py : le frontend (AgentAvatar) rend un avatar à partir
du seul (agent_id, name) sans registre, et `agent_models.py::AGENT_TIERS.get`
retombe proprement sur le tier "standard" pour un agent_id inconnu.
"""

from __future__ import annotations

from agents.base import LLMClient
from agents.rnd_council_close import RndCouncilCloseMixin
from agents.rnd_council_debate import RndCouncilDebateMixin
from agents.rnd_council_session import RndCouncilSessionMixin
from database.supabase_client import get_supabase


class RndCouncilAgent(
    RndCouncilCloseMixin,
    RndCouncilDebateMixin,
    RndCouncilSessionMixin,
):
    def __init__(self) -> None:
        self.db = get_supabase()
        self.llm = LLMClient()
