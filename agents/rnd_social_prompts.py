"""LLM prompts for R&D social pipeline (phase 5)."""

from __future__ import annotations

from config.agent_operating_spec import get_system_prompt

SOCIAL_STRATEGY_SYSTEM = get_system_prompt("rnd_social_strategy")
SOCIAL_POST_SYSTEM = get_system_prompt("rnd_social_post")
