"""R&D Agent — Alex Mercer. Thin facade for plan_executor / parallel_runner."""
from __future__ import annotations

from agents.agent_base import AgentBase

from typing import Any

from agents.base import LLMClient, log_agent_action, parse_json_response
from database.supabase_client import get_supabase
from skills.skill_agent_learning import inject_learning_context, record_task_learning
from config.agent_operating_spec import get_system_prompt
from skills.skill_langfuse import trace_agent


class RndAgent(AgentBase):
    """R&D lead — research and prototype specs via rnd_center / deep_research."""

    AGENT_NAME = "rnd_agent"
    SYSTEM_PROMPT = get_system_prompt("rnd_agent")

    def __init__(self, db=None, llm=None) -> None:
        self.db = db or get_supabase()
        self.llm = llm or LLMClient()

    @trace_agent("rnd_agent")
    def research_topic(self, query: str, context: str = "") -> dict[str, Any]:
        """Quick structured research on a market / product topic."""
        from services.deep_research import quick_research

        report = quick_research(
            query=query,
            context=context,
            agent_id=self.AGENT_NAME,
        )
        log_agent_action(
            self.db,
            self.AGENT_NAME,
            "research_topic",
            input_summary=query[:200],
            output_summary=str(report.get("executive_summary", ""))[:200],
        )
        try:
            record_task_learning(
                self.AGENT_NAME,
                "research_topic",
                str(report)[:400],
                success=True,
            )
        except Exception:
            pass
        return report

    @trace_agent("rnd_agent")
    def prototype_spec(self, idea: str, context: str = "") -> dict[str, Any]:
        """Turn a vetted idea into a lightweight prototype spec."""
        prompt = inject_learning_context(
            f"Idée : {idea}\nContexte : {context or '(aucun)'}\n"
            "Produis une spec prototype JSON : title, problem, solution, "
            "mvp_scope (3 bullets), risks (2), next_step.",
            self.AGENT_NAME,
            idea,
        )
        raw = self._complete(prompt, temperature=0.4)
        result = parse_json_response(raw)
        log_agent_action(
            self.db,
            self.AGENT_NAME,
            "prototype_spec",
            input_summary=idea[:200],
            output_summary=str(result.get("title", idea))[:200],
        )
        try:
            record_task_learning(
                self.AGENT_NAME,
                "prototype_spec",
                str(result)[:400],
                success=True,
            )
        except Exception:
            pass
        return result
