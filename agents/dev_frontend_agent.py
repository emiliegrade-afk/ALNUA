"""Minimal frontend agent for Hub web/UI dispatch."""

from __future__ import annotations

from typing import Any

from agents.agent_base import AgentBase
from config.agent_operating_spec import get_system_prompt


class DevFrontendAgent(AgentBase):
    AGENT_NAME = "dev_frontend"
    SYSTEM_PROMPT = get_system_prompt("dev_backend")

    def handle_instruction(self, instruction: str) -> dict[str, Any]:
        return {"status": "queued", "agent": self.AGENT_NAME, "instruction": instruction[:200]}

    def implement_ui(self, feature: str, context: str = "") -> dict[str, Any]:
        return {"summary": f"Implement UI for {feature}", "context": context[:200]}

    def fix_layout(self, issue: str, context: str = "") -> dict[str, Any]:
        return {"summary": f"Fix layout issue: {issue}", "context": context[:200]}
