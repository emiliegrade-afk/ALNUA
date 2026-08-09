"""Électronique Agent — Marco Ferreira, conception circuits ALNUA Robotique."""
from __future__ import annotations

from typing import Any

from agents.agent_base import AgentBase
from config.agent_operating_spec import get_system_prompt
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
        prompt = f"""Conçois un circuit électronique pour Eve robot.
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
}}"""
        return self.run_json_task(
            action="design_circuit",
            prompt=prompt,
            learning_key=circuit_name,
            input_summary=f"{circuit_name} | {function}",
            output_summary=lambda r: f"{len(r.get('components', []))} composants",
            temperature=0.3,
            max_tokens=2048,
        )

    @trace_agent("electronics")
    def bom_context(self, category: str | None = None, limit: int = 20) -> dict[str, Any]:
        """Attach live Eve BOM lines (or explicit unavailable) for circuit work."""
        from skills.skill_bom import get_bom_context

        return get_bom_context(category=category, limit=limit)

    @trace_agent("electronics")
    def suggest_alternatives(
        self,
        need: str,
        category: str | None = None,
        max_options: int = 4,
    ) -> dict[str, Any]:
        """Latest/cheaper component options grounded on Eve BOM (estimates only)."""
        from services.eve_sourcing import suggest_alternatives

        return suggest_alternatives(need, category=category, max_options=max_options)
