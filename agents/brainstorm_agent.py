"""Brainstorm Agent — partner d'idéation conversationnel pour Emilie.

Façade : mixins under ``agents/brainstorm_*.py`` keep each module ≤ ~300 lines.
"""
from __future__ import annotations

from agents.agent_base import AgentBase
from agents.brainstorm_chat import BrainstormChatMixin
from agents.brainstorm_constants import (  # noqa: F401 — public API re-export
    BRAINSTORM_NOTES_ROOT,
    WELCOME_MESSAGE,
)
from agents.brainstorm_legacy import BrainstormLegacyMixin
from agents.brainstorm_memory import BrainstormMemoryMixin
from agents.brainstorm_session import BrainstormSessionMixin
from config.agent_operating_spec import get_system_prompt


class BrainstormAgent(
    BrainstormLegacyMixin,
    BrainstormChatMixin,
    BrainstormMemoryMixin,
    BrainstormSessionMixin,
    AgentBase,
):
    AGENT_NAME = "brainstorm_agent"

    SYSTEM_PROMPT = get_system_prompt("brainstorm_ideas")

    SESSION_ACTIONS = ("session_start", "brainstorm_chat")
