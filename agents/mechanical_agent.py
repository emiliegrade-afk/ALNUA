"""Mécanique Agent — Ravi Chandrasekaran, conception mécanique ALNUA Robotique."""

from __future__ import annotations

from agents.agent_base import AgentBase

from typing import Any

from agents.base import log_agent_action, parse_json_response
from config.agent_operating_spec import get_system_prompt
from skills.skill_agent_learning import inject_learning_context, record_task_learning
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
        prompt = inject_learning_context(
            f"""Conçois une pièce mécanique pour Eve robot.
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
}}""",
            self.AGENT_NAME, part_name,
        )
        raw = self._complete(prompt, temperature=0.3, max_tokens=2048)
        result = parse_json_response(raw)
        log_agent_action(
            self.db, self.AGENT_NAME, "design_part",
            input_summary=f"{part_name} | {function}",
            output_summary=f"{len(result.get('tolerances', []))} tolérances définies",
        )
        try:
            record_task_learning(self.AGENT_NAME, "design_part", str(result)[:400], success=True)
        except Exception:
            pass
        return result
