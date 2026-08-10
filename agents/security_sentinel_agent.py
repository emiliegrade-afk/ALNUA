"""Security Sentinel Agent — Hugo Brandt, patrouille Hub ALNUA."""

from __future__ import annotations

from typing import Any

from agents.agent_base import AgentBase
from agents.base import log_agent_action
from config.agent_operating_spec import get_system_prompt
from skills.skill_langfuse import trace_agent


class SecuritySentinelAgent(AgentBase):
    AGENT_NAME = "security_sentinel"
    SYSTEM_PROMPT = get_system_prompt("security_sentinel")

    @trace_agent("security_sentinel")
    def patrol(self, *, notify: bool = True, auto_lockdown: bool | None = None) -> dict[str, Any]:
        from services.security_sentinel import run_patrol

        result = run_patrol(notify=notify, auto_lockdown=auto_lockdown)
        log_agent_action(
            self.db,
            self.AGENT_NAME,
            "patrol",
            input_summary=f"notify={notify}",
            output_summary=f"findings={len(result.get('findings') or [])} ok={result.get('ok')}",
        )
        return result

    @trace_agent("security_sentinel")
    def set_lockdown(self, active: bool, *, reason: str = "") -> dict[str, Any]:
        from services.security_sentinel import set_lockdown

        result = set_lockdown(active, reason=reason)
        log_agent_action(
            self.db,
            self.AGENT_NAME,
            "set_lockdown",
            input_summary=f"active={active}",
            output_summary=str(result)[:120],
        )
        return result

    @trace_agent("security_sentinel")
    def status(self) -> dict[str, Any]:
        from services.security_sentinel import is_lockdown_active, last_patrol

        return {
            "lockdown": is_lockdown_active(),
            "last_patrol": last_patrol(),
        }
