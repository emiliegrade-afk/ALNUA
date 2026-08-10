"""
rnd_committee_agent.py — Multi-agent R&D committee in natural language (phase 3).

Façade : mixins under ``agents/rnd_committee_*.py`` keep each module ≤ ~300 lines.
"""
from __future__ import annotations

from agents.agent_base import AgentBase
from agents.rnd_committee_close import RndCommitteeCloseMixin
from agents.rnd_committee_llm import RndCommitteeLlmMixin
from agents.rnd_committee_session import RndCommitteeSessionMixin
from services.rnd_committee import get_committee_repository
from services.rnd_repository import get_rnd_repository


class RndCommitteeAgent(
    RndCommitteeSessionMixin,
    RndCommitteeCloseMixin,
    RndCommitteeLlmMixin,
    AgentBase,
):
    AGENT_NAME = "rnd_committee_agent"

    def __init__(self) -> None:
        super().__init__()
        self.repo = get_rnd_repository()
        self.committee = get_committee_repository()
