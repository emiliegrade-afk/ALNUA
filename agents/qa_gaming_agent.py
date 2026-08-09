"""QA Gaming Agent — Tomás Freitas, tests gameplay ALNUA Gaming."""
from __future__ import annotations

from typing import Any

from agents.agent_base import AgentBase
from config.agent_operating_spec import get_system_prompt
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
        prompt = f"""Construis un plan de test pour {game}.
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
}}"""
        return self.run_json_task(
            action="build_test_plan",
            prompt=prompt,
            learning_key=feature_name,
            input_summary=f"{game} | {feature_name} | {build_version}",
            output_summary=lambda r: f"{len(r.get('test_cases', []))} cas de test",
            temperature=0.4,
            max_tokens=3072,
        )
