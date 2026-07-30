"""QA Robot Agent — Bilal Nasser, tests hardware ALNUA Robotique."""

from __future__ import annotations

from agents.agent_base import AgentBase

from typing import Any

from agents.base import log_agent_action, parse_json_response
from config.agent_operating_spec import get_system_prompt
from skills.skill_agent_learning import inject_learning_context, record_task_learning
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
        prompt = inject_learning_context(
            f"""Construis un protocole de test hardware pour Eve robot.
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
}}""",
            self.AGENT_NAME, subsystem_name,
        )
        raw = self._complete(prompt, temperature=0.4, max_tokens=2048)
        result = parse_json_response(raw)
        log_agent_action(
            self.db, self.AGENT_NAME, "build_test_protocol",
            input_summary=f"{subsystem_name} | {risk_level}",
            output_summary=f"{len(result.get('test_steps', []))} étapes de test",
        )
        try:
            record_task_learning(self.AGENT_NAME, "build_test_protocol", str(result)[:400], success=True)
        except Exception:
            pass
        return result
