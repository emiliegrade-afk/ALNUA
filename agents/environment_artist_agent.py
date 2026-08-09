"""Environment Artist Agent — Priya Nandan, habillage niveaux ALNUA Gaming."""
from __future__ import annotations

from typing import Any

from agents.agent_base import AgentBase
from config.agent_operating_spec import get_system_prompt
from skills.skill_langfuse import trace_agent


class EnvironmentArtistAgent(AgentBase):
    AGENT_NAME = "environment_artist"
    SYSTEM_PROMPT = get_system_prompt("environment_artist")

    @trace_agent("environment_artist")
    def design_environment(
        self,
        zone_name: str,
        game: str,
        biome: str = "",
        mood: str = "",
    ) -> dict[str, Any]:
        """Conçoit l'habillage (props, végétation, architecture) d'une zone."""
        prompt = f"""Conçois l'habillage visuel d'une zone pour {game}.
Zone : {zone_name}
Biome : {biome or 'À définir avec Finn Larsen'}
Ambiance recherchée : {mood or 'Cohérente avec le lore Wyrdheim'}

Réponds en JSON :
{{
  "zone": "{zone_name}",
  "biome": "{biome}",
  "prop_categories": [{{ "category": "string", "examples": ["string"], "density": "faible|moyenne|élevée" }}],
  "architecture_notes": "Style architectural et matériaux dominants",
  "lighting_mood": "string",
  "perf_notes": "Points d'attention perf (instancing, LOD, densité)",
  "handoff_notes": "Notes pour Finn Larsen (flow des niveaux)"
}}"""
        return self.run_json_task(
            action="design_environment",
            prompt=prompt,
            learning_key=zone_name,
            input_summary=f"{game} | {zone_name} | {biome}",
            output_summary=lambda r: f"{len(r.get('prop_categories', []))} catégories de props",
            temperature=0.7,
            max_tokens=3072,
        )
