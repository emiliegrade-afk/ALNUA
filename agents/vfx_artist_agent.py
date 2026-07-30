"""VFX Artist Agent — Diego Salas, effets visuels ALNUA Gaming."""

from __future__ import annotations

from agents.agent_base import AgentBase

from typing import Any

from agents.base import log_agent_action, parse_json_response
from config.agent_operating_spec import get_system_prompt
from skills.skill_agent_learning import inject_learning_context, record_task_learning
from skills.skill_langfuse import trace_agent


class VfxArtistAgent(AgentBase):
    AGENT_NAME = "vfx_artist"

    SYSTEM_PROMPT = get_system_prompt("vfx_artist")

    @trace_agent("vfx_artist")
    def design_vfx(
        self,
        effect_name: str,
        game: str,
        trigger: str = "",
        style: str = "",
    ) -> dict[str, Any]:
        """Conçoit un effet visuel Niagara (impact, sort, ambiance)."""
        prompt = inject_learning_context(
            f"""Conçois un effet visuel pour {game}.
Effet : {effect_name}
Déclencheur : {trigger or 'À définir (impact, cast, ambiance)'}
Style recherché : {style or 'Cohérent avec la direction artistique Wyrdheim'}

Réponds en JSON :
{{
  "effect": "{effect_name}",
  "trigger": "{trigger}",
  "niagara_modules": [{{ "module": "string", "purpose": "string" }}],
  "readability_notes": "Comment l'effet communique l'action au joueur",
  "gpu_cost_estimate": "faible|moyen|élevé",
  "handoff_notes": "Notes pour Otto Reindl (budget perf) et Ingrid Halvorsen (synchro son)"
}}""",
            self.AGENT_NAME, effect_name,
        )
        raw = self._complete(prompt, temperature=0.7, max_tokens=2048)
        result = parse_json_response(raw)
        log_agent_action(
            self.db, self.AGENT_NAME, "design_vfx",
            input_summary=f"{game} | {effect_name} | {trigger}",
            output_summary=f"{len(result.get('niagara_modules', []))} modules Niagara",
        )
        try:
            record_task_learning(self.AGENT_NAME, "design_vfx", str(result)[:400], success=True)
        except Exception:
            pass
        return result
