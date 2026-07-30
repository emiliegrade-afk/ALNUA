"""Firmware Agent — Petra Vogel, temps réel embarqué ALNUA Robotique."""

from __future__ import annotations

from agents.agent_base import AgentBase

from typing import Any

from agents.base import log_agent_action, parse_json_response
from config.agent_operating_spec import get_system_prompt
from skills.skill_agent_learning import inject_learning_context, record_task_learning
from skills.skill_langfuse import trace_agent


class FirmwareAgent(AgentBase):
    AGENT_NAME = "firmware"

    SYSTEM_PROMPT = get_system_prompt("firmware")

    @trace_agent("firmware")
    def design_driver(
        self,
        component_name: str,
        timing_requirement: str = "",
        constraints: str = "",
    ) -> dict[str, Any]:
        """Conçoit un driver bas niveau temps réel pour un composant (capteur/moteur)."""
        prompt = inject_learning_context(
            f"""Conçois un driver firmware bas niveau pour Eve robot.
Composant : {component_name}
Contrainte de timing : {timing_requirement or 'À définir'}
Contraintes : {constraints or 'Microcontrôleur embarqué, C bas niveau'}

Réponds en JSON :
{{
  "component": "{component_name}",
  "timing_requirement": "{timing_requirement}",
  "driver_design": [{{ "step": "string", "detail": "string" }}],
  "interrupt_strategy": "Stratégie d'interruption / polling recommandée",
  "risk_notes": "Risques de race condition ou de latence",
  "handoff_notes": "Notes pour Zara Singh (embedded_dev) — interface Python"
}}""",
            self.AGENT_NAME, component_name,
        )
        raw = self._complete(prompt, temperature=0.3, max_tokens=2048)
        result = parse_json_response(raw)
        log_agent_action(
            self.db, self.AGENT_NAME, "design_driver",
            input_summary=f"{component_name} | {timing_requirement}",
            output_summary=f"{len(result.get('driver_design', []))} étapes de conception",
        )
        try:
            record_task_learning(self.AGENT_NAME, "design_driver", str(result)[:400], success=True)
        except Exception:
            pass
        return result
