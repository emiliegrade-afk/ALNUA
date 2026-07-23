"""Example plugin agent — template for marketplace packs."""

from __future__ import annotations

from typing import Any


class PluginAgent:
    AGENT_NAME = "example_echo"

    def run(self, message: str) -> dict[str, Any]:
        return {"echo": message, "agent": self.AGENT_NAME}
