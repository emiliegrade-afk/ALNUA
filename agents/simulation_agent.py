"""Simulation Agent — Haruto Ishikawa, modélisation & simulation ALNUA Robotique."""

from __future__ import annotations

from agents.agent_base import AgentBase

from typing import Any

from agents.base import log_agent_action, parse_json_response
from config.agent_operating_spec import get_system_prompt
from skills.skill_agent_learning import inject_learning_context, record_task_learning
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
        prompt = inject_learning_context(
            f"""Construis un plan de simulation pour Eve robot.
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
}}""",
            self.AGENT_NAME, subsystem_name,
        )
        raw = self._complete(prompt, temperature=0.3, max_tokens=2048)
        result = parse_json_response(raw)
        log_agent_action(
            self.db, self.AGENT_NAME, "run_simulation_plan",
            input_summary=f"{subsystem_name} | {scenario}",
            output_summary=f"{len(result.get('simulation_steps', []))} étapes de simulation",
        )
        try:
            record_task_learning(self.AGENT_NAME, "run_simulation_plan", str(result)[:400], success=True)
        except Exception:
            pass
        return result
