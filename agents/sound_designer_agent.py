"""Sound Designer Agent — Ingrid Halvorsen, ambiances sonores ALNUA Gaming."""
from __future__ import annotations

from typing import Any

from agents.agent_base import AgentBase
from config.agent_operating_spec import get_system_prompt
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
        prompt = f"""Conçois l'ambiance sonore d'une scène pour {game}.
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
}}"""
        return self.run_json_task(
            action="design_soundscape",
            prompt=prompt,
            learning_key=scene_name,
            input_summary=f"{game} | {scene_name} | {mood}",
            output_summary=lambda r: f"{len(r.get('ambient_layers', []))} couches d'ambiance",
            temperature=0.7,
            max_tokens=2048,
        )
