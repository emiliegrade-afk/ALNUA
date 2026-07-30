"""Électronique Agent — Marco Ferreira, conception circuits ALNUA Robotique."""

from __future__ import annotations

from agents.agent_base import AgentBase

from typing import Any

from agents.base import log_agent_action, parse_json_response
from config.agent_operating_spec import get_system_prompt
from skills.skill_agent_learning import inject_learning_context, record_task_learning
from skills.skill_langfuse import trace_agent


class ElectronicsAgent(AgentBase):
    AGENT_NAME = "electronics"

    SYSTEM_PROMPT = get_system_prompt("electronics")

    @trace_agent("electronics")
    def design_circuit(
        self,
        circuit_name: str,
        function: str = "",
        constraints: str = "",
    ) -> dict[str, Any]:
        """Conçoit un schéma électronique protégé pour un sous-système d'Eve."""
        prompt = inject_learning_context(
            f"""Conçois un circuit électronique pour Eve robot.
Circuit : {circuit_name}
Fonction : {function or 'À définir'}
Contraintes : {constraints or 'Alimentation Pi 5V/3.3V, protections standard'}

Réponds en JSON :
{{
  "circuit": "{circuit_name}",
  "function": "{function}",
  "components": [{{ "component": "string", "spec": "string", "qty": 1 }}],
  "protections": ["Protections prévues (surtension, court-circuit, thermique)"],
  "pcb_notes": "Contraintes de routage PCB",
  "handoff_notes": "Notes pour Yuki Tanaka (BOM) et Petra Vogel (firmware)"
}}""",
            self.AGENT_NAME, circuit_name,
        )
        raw = self._complete(prompt, temperature=0.3, max_tokens=2048)
        result = parse_json_response(raw)
        log_agent_action(
            self.db, self.AGENT_NAME, "design_circuit",
            input_summary=f"{circuit_name} | {function}",
            output_summary=f"{len(result.get('components', []))} composants",
        )
        try:
            record_task_learning(self.AGENT_NAME, "design_circuit", str(result)[:400], success=True)
        except Exception:
            pass
        return result
