"""
agent_system_prompts.py — Compiled prompts from 9-layer operating specs.

Source: config/agent_operating_spec.py + config/agent_specs_registry.py
"""

from __future__ import annotations

from config.agent_operating_spec import (
    compile_system_prompt,
    crew_backstory,
    get_operating_spec,
    get_system_prompt,
)

# Backward-compatible exports
RND_AGENT_SYSTEM_PROMPT = get_system_prompt("rnd_agent")
BRAINSTORM_CHAT_PROMPT = get_system_prompt("brainstorm")
BRAINSTORM_SUMMARIZE_PROMPT = get_system_prompt("brainstorm_summarize")
CONTENT_SYSTEM_PROMPT = get_system_prompt("content")
ACCOUNTING_SYSTEM_PROMPT = get_system_prompt("accounting")
MARKETING_BACKSTORY_BODY = get_system_prompt("marketing")
GAME_DIRECTOR_BACKSTORY_BODY = get_system_prompt("game_director")
DEV_GAMING_BACKSTORY_BODY = get_system_prompt("dev_gaming")
HARDWARE_BACKSTORY_BODY = get_system_prompt("hardware")
EMBEDDED_DEV_BACKSTORY_BODY = get_system_prompt("embedded_dev")

__all__ = [
    "compile_system_prompt",
    "crew_backstory",
    "get_operating_spec",
    "get_system_prompt",
    "RND_AGENT_SYSTEM_PROMPT",
    "BRAINSTORM_CHAT_PROMPT",
    "BRAINSTORM_SUMMARIZE_PROMPT",
    "CONTENT_SYSTEM_PROMPT",
    "ACCOUNTING_SYSTEM_PROMPT",
    "MARKETING_BACKSTORY_BODY",
    "GAME_DIRECTOR_BACKSTORY_BODY",
    "DEV_GAMING_BACKSTORY_BODY",
    "HARDWARE_BACKSTORY_BODY",
    "EMBEDDED_DEV_BACKSTORY_BODY",
]
