"""Sound Designer Agent — Ingrid Halvorsen, ambiances sonores ALNUA Gaming."""

from __future__ import annotations

from agents.agent_base import AgentBase

from typing import Any

from agents.base import log_agent_action, parse_json_response
from config.agent_operating_spec import get_system_prompt
from skills.skill_agent_learning import inject_learning_context, record_task_learning
from skills.skill_langfuse import trace_agent


class SoundDesignerAgent(AgentBase):
    AGENT_NAME = "sound_designer"

    SYSTEM_PROMPT = get_system_prompt("sound_designer")

    @trace_agent("sound_designer")
    def design_soundscape(
        self,
        scene_name: str,
        game: str,
        mood: str = "",
        key_sfx: str = "",
    ) -> dict[str, Any]:
        """Conçoit l'ambiance sonore et les SFX clés d'une scène/zone."""
        prompt = inject_learning_context(
            f"""Conçois l'ambiance sonore d'une scène pour {game}.
Scène : {scene_name}
Ambiance recherchée : {mood or 'Cohérente avec le biome et le lore'}
SFX clés attendus : {key_sfx or 'À définir'}

Réponds en JSON :
{{
  "scene": "{scene_name}",
  "ambient_layers": [{{ "layer": "string", "description": "string", "loop": true }}],
  "key_sfx": [{{ "trigger": "string", "description": "string" }}],
  "mixing_notes": "Hiérarchie sonore (priorité entre ambiance/SFX/musique)",
  "handoff_notes": "Notes pour Diego Salas (synchro VFX)"
}}""",
            self.AGENT_NAME, scene_name,
        )
        raw = self._complete(prompt, temperature=0.7, max_tokens=2048)
        result = parse_json_response(raw)
        log_agent_action(
            self.db, self.AGENT_NAME, "design_soundscape",
            input_summary=f"{game} | {scene_name} | {mood}",
            output_summary=f"{len(result.get('ambient_layers', []))} couches d'ambiance",
        )
        try:
            record_task_learning(self.AGENT_NAME, "design_soundscape", str(result)[:400], success=True)
        except Exception:
            pass
        return result
