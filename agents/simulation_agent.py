"""Simulation Agent — Haruto Ishikawa, modélisation & simulation ALNUA Robotique."""
from __future__ import annotations

from typing import Any

from agents.agent_base import AgentBase
from config.agent_operating_spec import get_system_prompt
from skills.skill_langfuse import trace_agent


class SimulationAgent(AgentBase):
    AGENT_NAME = "simulation"
    SYSTEM_PROMPT = get_system_prompt("simulation")

    @trace_agent("simulation")
    def run_simulation_plan(
        self,
        subsystem_name: str,
        scenario: str = "",
        constraints: str = "",
    ) -> dict[str, Any]:
        """Construit un plan de simulation numérique avant prototypage physique."""
        prompt = f"""Construis un plan de simulation pour Eve robot.
Sous-système : {subsystem_name}
Scénario à valider : {scenario or 'À définir'}
Contraintes connues : {constraints or 'Aucune signalée'}

Réponds en JSON :
{{
  "subsystem": "{subsystem_name}",
  "scenario": "{scenario}",
  "simulation_steps": [{{ "step": "string", "tool_or_method": "string" }}],
  "expected_failure_modes": ["Défauts que la simulation devrait révéler"],
  "confidence_level": "faible|moyen|élevé",
  "recommendation": "go|no-go prototype physique, avec justification"
}}"""
        return self.run_json_task(
            action="run_simulation_plan",
            prompt=prompt,
            learning_key=subsystem_name,
            input_summary=f"{subsystem_name} | {scenario}",
            output_summary=lambda r: f"{len(r.get('simulation_steps', []))} étapes de simulation",
            temperature=0.3,
            max_tokens=2048,
        )
