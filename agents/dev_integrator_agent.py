"""Minimal integrator agent for worktree merge and smoke checks."""

from __future__ import annotations

from typing import Any

from agents.agent_base import AgentBase
from config.agent_operating_spec import get_system_prompt


class DevIntegratorAgent(AgentBase):
    AGENT_NAME = "dev_integrator"
    SYSTEM_PROMPT = get_system_prompt("dev_backend")

    def integrate_worktrees(self, branch: str, worktrees: list[str] | None = None) -> dict[str, Any]:
        return {"status": "integrated", "branch": branch, "worktrees": worktrees or []}

    def open_integration_pr(self, branch: str, title: str) -> dict[str, Any]:
        return {"status": "pr_ready", "branch": branch, "title": title}

    def review_diff(self, diff_summary: str) -> dict[str, Any]:
        return {"status": "reviewed", "summary": diff_summary[:200]}
