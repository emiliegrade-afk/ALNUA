"""AI Programmer Agent — Kenji Sato, IA comportementale ALNUA Gaming."""
from __future__ import annotations

from typing import Any

from agents.agent_base import AgentBase
from config.agent_operating_spec import get_system_prompt
from skills.skill_langfuse import trace_agent


class AiProgrammerAgent(AgentBase):
    AGENT_NAME = "ai_programmer"
    SYSTEM_PROMPT = get_system_prompt("ai_programmer")

    @trace_agent("ai_programmer")
    def design_behavior(
        self,
        entity_name: str,
        game: str,
        behavior_type: str = "hostile",
        difficulty: str = "medium",
    ) -> dict[str, Any]:
        """Conçoit un behavior tree pour une entité IA (ennemi, PNJ, faune)."""
        prompt = f"""Conçois un comportement IA pour {game}.
Entité : {entity_name}
Type de comportement : {behavior_type} (hostile|défensif|patrouille|passif)
Difficulté : {difficulty} (easy|medium|hard|boss)

Réponds en JSON :
{{
  "entity": "{entity_name}",
  "behavior_type": "{behavior_type}",
  "behavior_tree": [
    {{ "node": "string", "type": "selector|sequence|action|condition", "description": "string" }}
  ],
  "blackboard_keys": ["string"],
  "navmesh_notes": "Contraintes de navigation à prévoir",
  "failure_modes": ["Cas limites à surveiller (ex: coincé dans le décor)"],
  "handoff_notes": "Notes pour Tomás Freitas (QA gameplay)"
}}"""
        return self.run_json_task(
            action="design_behavior",
            prompt=prompt,
            learning_key=entity_name,
            input_summary=f"{game} | {entity_name} | {behavior_type}",
            output_summary=lambda r: f"{len(r.get('behavior_tree', []))} nœuds de comportement",
            temperature=0.5,
            max_tokens=3072,
        )
