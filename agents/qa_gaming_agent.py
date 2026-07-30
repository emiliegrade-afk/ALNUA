"""QA Gaming Agent — Tomás Freitas, tests gameplay ALNUA Gaming."""

from __future__ import annotations

from agents.agent_base import AgentBase

from typing import Any

from agents.base import log_agent_action, parse_json_response
from config.agent_operating_spec import get_system_prompt
from skills.skill_agent_learning import inject_learning_context, record_task_learning
from skills.skill_langfuse import trace_agent


class QaGamingAgent(AgentBase):
    AGENT_NAME = "qa_gaming"

    SYSTEM_PROMPT = get_system_prompt("qa_gaming")

    @trace_agent("qa_gaming")
    def build_test_plan(
        self,
        feature_name: str,
        game: str,
        build_version: str = "",
        risk_areas: str = "",
    ) -> dict[str, Any]:
        """Construit un plan de test pour une feature ou un build avant validation."""
        prompt = inject_learning_context(
            f"""Construis un plan de test pour {game}.
Feature/build : {feature_name}
Version : {build_version or 'non précisée'}
Zones à risque signalées : {risk_areas or 'Aucune signalée — couverture standard'}

Réponds en JSON :
{{
  "feature": "{feature_name}",
  "build_version": "{build_version}",
  "test_cases": [{{ "id": 1, "scenario": "string", "expected": "string", "priority": "critical|high|medium|low" }}],
  "regression_focus": ["Zones à re-tester en priorité"],
  "known_risk_areas": ["string"],
  "exit_criteria": "Critère de fin de test (ex: 0 bug bloquant, N bugs mineurs acceptés)"
}}""",
            self.AGENT_NAME, feature_name,
        )
        raw = self._complete(prompt, temperature=0.4, max_tokens=3072)
        result = parse_json_response(raw)
        log_agent_action(
            self.db, self.AGENT_NAME, "build_test_plan",
            input_summary=f"{game} | {feature_name} | {build_version}",
            output_summary=f"{len(result.get('test_cases', []))} cas de test",
        )
        try:
            record_task_learning(self.AGENT_NAME, "build_test_plan", str(result)[:400], success=True)
        except Exception:
            pass
        return result
