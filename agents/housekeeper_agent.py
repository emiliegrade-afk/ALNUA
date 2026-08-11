"""Housekeeper Agent — Clara Nest, range le PC avec quarantaine."""

from __future__ import annotations

from typing import Any

from agents.agent_base import AgentBase
from agents.base import log_agent_action
from config.agent_operating_spec import get_system_prompt
from skills.skill_langfuse import trace_agent


class HousekeeperAgent(AgentBase):
    AGENT_NAME = "housekeeper"
    SYSTEM_PROMPT = get_system_prompt("housekeeper")

    @trace_agent("housekeeper")
    def scan(self, extra_roots: list[str] | None = None) -> dict[str, Any]:
        from services.pc_housekeeper import resolve_roots, scan_clutter

        roots = resolve_roots(extra_roots)
        result = scan_clutter(roots)
        log_agent_action(
            self.db,
            self.AGENT_NAME,
            "scan",
            input_summary=str(len(roots)),
            output_summary=f"items={result.get('count')}",
        )
        return result

    @trace_agent("housekeeper")
    def propose(self) -> dict[str, Any]:
        from services.pc_housekeeper import propose_organization

        result = propose_organization()
        log_agent_action(
            self.db,
            self.AGENT_NAME,
            "propose",
            input_summary="auto",
            output_summary=f"n={len(result.get('proposals') or [])}",
        )
        return result

    @trace_agent("housekeeper")
    def apply(self, proposals: list[dict[str, Any]] | None = None, *, dry_run: bool = False) -> dict[str, Any]:
        from services.pc_housekeeper import apply_proposals, propose_organization

        props = proposals
        if props is None:
            props = (propose_organization().get("proposals") or [])
        return apply_proposals(props, dry_run=dry_run)

    @trace_agent("housekeeper")
    def quarantine(self, paths: list[str]) -> dict[str, Any]:
        from services.pc_housekeeper import quarantine_for_delete

        return quarantine_for_delete(paths)

    @trace_agent("housekeeper")
    def status(self) -> dict[str, Any]:
        from services.pc_housekeeper import status

        return status()
