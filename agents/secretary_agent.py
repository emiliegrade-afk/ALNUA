"""Secretary Agent — Nadia Faure, Secrétaire de Direction ALNUA.

Façade : mixins under ``agents/secretary_*.py`` keep each module ≤ ~300 lines.
"""
from __future__ import annotations

from agents.agent_base import AgentBase
from agents.secretary_documents import SecretaryDocumentsMixin
from agents.secretary_handlers_comms import SecretaryHandlersCommsMixin
from agents.secretary_handlers_ops import SecretaryHandlersOpsMixin
from agents.secretary_instruction import SecretaryInstructionMixin
from config.agent_operating_spec import get_system_prompt


class SecretaryAgent(
    SecretaryInstructionMixin,
    SecretaryHandlersCommsMixin,
    SecretaryHandlersOpsMixin,
    SecretaryDocumentsMixin,
    AgentBase,
):
    AGENT_NAME = "secretary"

    SYSTEM_PROMPT = get_system_prompt("secretary")
