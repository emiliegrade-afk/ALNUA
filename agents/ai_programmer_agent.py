"""AI Programmer Agent — Kenji Sato, IA comportementale ALNUA Gaming."""

from __future__ import annotations

from agents.agent_base import AgentBase

from typing import Any

from agents.base import log_agent_action, parse_json_response
from config.agent_operating_spec import get_system_prompt
from skills.skill_agent_learning import inject_learning_context, record_task_learning
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
        prompt = inject_learning_context(
            f"""Conçois un comportement IA pour {game}.
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
}}""",
            self.AGENT_NAME, entity_name,
        )
        raw = self._complete(prompt, temperature=0.5, max_tokens=3072)
        result = parse_json_response(raw)
        log_agent_action(
            self.db, self.AGENT_NAME, "design_behavior",
            input_summary=f"{game} | {entity_name} | {behavior_type}",
            output_summary=f"{len(result.get('behavior_tree', []))} nœuds de comportement",
        )
        try:
            record_task_learning(self.AGENT_NAME, "design_behavior", str(result)[:400], success=True)
        except Exception:
            pass
        return result
