"""Safety Agent — Clara Dubois, sécurité produit ALNUA Robotique."""
from __future__ import annotations

from typing import Any

from agents.agent_base import AgentBase
from config.agent_operating_spec import get_system_prompt
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
        prompt = f"""Analyse les risques de sécurité pour Eve robot.
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
}}"""
        return self.run_json_task(
            action="assess_risk",
            prompt=prompt,
            learning_key=subsystem_name,
            input_summary=f"{subsystem_name} | {hazard_type}",
            output_summary=lambda r: f"{len(r.get('hazards', []))} risques identifiés",
            temperature=0.3,
            max_tokens=2048,
        )

    @trace_agent("safety")
    def lab_context(
        self,
        project_id: str | None = None,
        category: str | None = None,
    ) -> dict[str, Any]:
        """Vague B — lab + builds grounding for risk assessment (no invented fails)."""
        from skills.skill_robo_lab import get_lab_bundle

        return get_lab_bundle(project_id=project_id, category=category)
