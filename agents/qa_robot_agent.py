"""QA Robot Agent — Bilal Nasser, tests hardware ALNUA Robotique."""
from __future__ import annotations

from typing import Any

from agents.agent_base import AgentBase
from config.agent_operating_spec import get_system_prompt
from skills.skill_langfuse import trace_agent


class QaRobotAgent(AgentBase):
    AGENT_NAME = "qa_robot"
    SYSTEM_PROMPT = get_system_prompt("qa_robot")

    @trace_agent("qa_robot")
    def build_test_protocol(
        self,
        subsystem_name: str,
        risk_level: str = "medium",
        prior_issues: str = "",
    ) -> dict[str, Any]:
        """Construit un protocole de test hardware reproductible pour un sous-système d'Eve."""
        prompt = f"""Construis un protocole de test hardware pour Eve robot.
Sous-système : {subsystem_name}
Niveau de risque : {risk_level} (low|medium|high)
Problèmes antérieurs : {prior_issues or 'Aucun connu'}

Réponds en JSON :
{{
  "subsystem": "{subsystem_name}",
  "risk_level": "{risk_level}",
  "test_steps": [{{ "step": "string", "expected": "string", "bench_needed": "string" }}],
  "regression_focus": ["Points à re-tester après toute modification"],
  "safety_check_required": true,
  "exit_criteria": "Critère de validation du sous-système"
}}"""
        return self.run_json_task(
            action="build_test_protocol",
            prompt=prompt,
            learning_key=subsystem_name,
            input_summary=f"{subsystem_name} | {risk_level}",
            output_summary=lambda r: f"{len(r.get('test_steps', []))} étapes de test",
            temperature=0.4,
            max_tokens=2048,
        )
