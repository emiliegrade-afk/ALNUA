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

    def run_json_task(
        self,
        *,
        action: str,
        prompt: str,
        learning_key: str,
        input_summary: str,
        output_summary: str | Any = "",
        temperature: float = 0.5,
        max_tokens: int = 2048,
    ) -> dict[str, Any]:
        """
        Shared one-shot JSON task path used by Phase-13 specialty agents.

        Callers still own ``@trace_agent`` and the domain prompt; this helper
        owns learning inject, complete, parse, log, and learning record.
        ``output_summary`` may be a static string or ``callable(result) -> str``.
        """
        from collections.abc import Callable

        from skills.skill_agent_learning import inject_learning_context, record_task_learning

        wrapped = inject_learning_context(prompt, self.AGENT_NAME, learning_key)
        raw = self._complete(wrapped, temperature=temperature, max_tokens=max_tokens)
        result = parse_json_response(raw)
        if callable(output_summary):
            summary_fn: Callable[[dict[str, Any]], str] = output_summary
            out = summary_fn(result)
        else:
            out = str(output_summary or str(result)[:100])
        log_agent_action(
            self.db,
            self.AGENT_NAME,
            action,
            input_summary=input_summary,
            output_summary=out,
        )
        try:
            record_task_learning(
                self.AGENT_NAME, action, str(result)[:400], success=True
            )
        except Exception:
            pass
        return result


__all__ = ["AgentBase", "parse_json_response"]
