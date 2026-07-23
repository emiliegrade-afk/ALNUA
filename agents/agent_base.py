"""Base class for ALNUA agents — canonical LLM ids + async helpers."""

from __future__ import annotations

import inspect
from typing import Any

from agents.base import LLMClient, log_agent_action, parse_json_response
from config.agent_models import memory_agent_id, normalize_agent_id
from database.supabase_client import SupabaseClient, get_supabase


class AgentBase:
    """Shared agent wiring: DB, LLM, normalized agent_id for routing/costs."""

    AGENT_NAME: str = "unknown"
    SYSTEM_PROMPT: str = ""

    def __init__(
        self,
        db: SupabaseClient | None = None,
        llm: LLMClient | None = None,
    ) -> None:
        self.db = db or get_supabase()
        self.llm = llm or LLMClient()

    @property
    def llm_agent_id(self) -> str:
        """Canonical id for model routing (coo not coo_agent, qa not qa_agent)."""
        return normalize_agent_id(self.AGENT_NAME)

    @property
    def memory_agent_id(self) -> str:
        return memory_agent_id(self.AGENT_NAME)

    def _caller_method(self) -> str:
        frame = inspect.currentframe()
        if frame and frame.f_back:
            return frame.f_back.f_code.co_name
        return "run"

    def _complete(
        self,
        user: str,
        *,
        system_prompt: str | None = None,
        agent_id: str | None = None,
        method_name: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
    ) -> str:
        return self.llm.complete(
            system_prompt or self.SYSTEM_PROMPT,
            user,
            agent_id=agent_id or self.llm_agent_id,
            method_name=method_name or self._caller_method(),
            temperature=temperature,
            max_tokens=max_tokens,
        )

    async def _complete_async(
        self,
        user: str,
        *,
        system_prompt: str | None = None,
        agent_id: str | None = None,
        method_name: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
    ) -> str:
        return await self.llm.complete_async(
            system_prompt or self.SYSTEM_PROMPT,
            user,
            agent_id=agent_id or self.llm_agent_id,
            method_name=method_name or self._caller_method(),
            temperature=temperature,
            max_tokens=max_tokens,
        )

    def _log(
        self,
        action: str,
        input_summary: str,
        output_summary: str,
        *,
        status: str = "success",
        project_id: str | None = None,
    ) -> dict[str, Any]:
        return log_agent_action(
            self.db,
            self.memory_agent_id,
            action,
            input_summary,
            output_summary,
            status=status,
            project_id=project_id,
        )


__all__ = ["AgentBase", "parse_json_response"]
