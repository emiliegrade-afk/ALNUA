"""Firmware Agent — Petra Vogel, temps réel embarqué ALNUA Robotique."""
from __future__ import annotations

from typing import Any

from agents.agent_base import AgentBase
from config.agent_operating_spec import get_system_prompt
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
        prompt = f"""Conçois un driver firmware bas niveau pour Eve robot.
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
}}"""
        return self.run_json_task(
            action="design_driver",
            prompt=prompt,
            learning_key=component_name,
            input_summary=f"{component_name} | {timing_requirement}",
            output_summary=lambda r: f"{len(r.get('driver_design', []))} étapes de conception",
            temperature=0.3,
            max_tokens=2048,
        )
