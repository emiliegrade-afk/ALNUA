"""Safety Agent — Clara Dubois, sécurité produit ALNUA Robotique."""

from __future__ import annotations

from agents.agent_base import AgentBase

from typing import Any

from agents.base import log_agent_action, parse_json_response
from config.agent_operating_spec import get_system_prompt
from skills.skill_agent_learning import inject_learning_context, record_task_learning
from skills.skill_langfuse import trace_agent


class SafetyAgent(AgentBase):
    AGENT_NAME = "safety"

    SYSTEM_PROMPT = get_system_prompt("safety")

    @trace_agent("safety")
    def assess_risk(
        self,
        subsystem_name: str,
        hazard_type: str = "",
        context: str = "",
    ) -> dict[str, Any]:
        """Analyse les risques physiques d'un sous-système et propose des mitigations."""
        prompt = inject_learning_context(
            f"""Analyse les risques de sécurité pour Eve robot.
Sous-système : {subsystem_name}
Type de risque : {hazard_type or 'À identifier (batterie, moteur, chaleur, mécanique)'}
Contexte : {context or 'Aucun contexte additionnel'}

Réponds en JSON :
{{
  "subsystem": "{subsystem_name}",
  "hazards": [{{ "hazard": "string", "probability": "low|medium|high", "severity": "low|medium|high|critical" }}],
  "mitigations": [{{ "action": "string", "hazard_addressed": "string" }}],
  "operational_limits": "Limites opérationnelles sûres à respecter",
  "test_go_no_go": "go|no-go avant test à risque, avec justification"
}}""",
            self.AGENT_NAME, subsystem_name,
        )
        raw = self._complete(prompt, temperature=0.3, max_tokens=2048)
        result = parse_json_response(raw)
        log_agent_action(
            self.db, self.AGENT_NAME, "assess_risk",
            input_summary=f"{subsystem_name} | {hazard_type}",
            output_summary=f"{len(result.get('hazards', []))} risques identifiés",
        )
        try:
            record_task_learning(self.AGENT_NAME, "assess_risk", str(result)[:400], success=True)
        except Exception:
            pass
        return result
