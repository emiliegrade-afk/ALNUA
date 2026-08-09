"""Mécanique Agent — Ravi Chandrasekaran, conception mécanique ALNUA Robotique."""
from __future__ import annotations

from typing import Any

from agents.agent_base import AgentBase
from config.agent_operating_spec import get_system_prompt
from skills.skill_langfuse import trace_agent


class MechanicalAgent(AgentBase):
    AGENT_NAME = "mechanical"
    SYSTEM_PROMPT = get_system_prompt("mechanical")

    @trace_agent("mechanical")
    def design_part(
        self,
        part_name: str,
        function: str = "",
        load_requirements: str = "",
    ) -> dict[str, Any]:
        """Conçoit une pièce mécanique avec tolérances et contraintes structurelles."""
        prompt = f"""Conçois une pièce mécanique pour Eve robot.
Pièce : {part_name}
Fonction : {function or 'À définir'}
Contraintes de charge : {load_requirements or 'À définir'}

Réponds en JSON :
{{
  "part": "{part_name}",
  "function": "{function}",
  "material": "Matériau recommandé et pourquoi",
  "tolerances": [{{ "feature": "string", "tolerance_mm": 0.1, "reason": "string" }}],
  "assembly_notes": "Contraintes d'assemblage répétable",
  "handoff_notes": "Notes pour Elin Bergström (esthétique) et Haruto Ishikawa (simulation avant fabrication)"
}}"""
        return self.run_json_task(
            action="design_part",
            prompt=prompt,
            learning_key=part_name,
            input_summary=f"{part_name} | {function}",
            output_summary=lambda r: f"{len(r.get('tolerances', []))} tolérances définies",
            temperature=0.3,
            max_tokens=2048,
        )
