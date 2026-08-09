"""VFX Artist Agent — Diego Salas, effets visuels ALNUA Gaming."""
from __future__ import annotations

from typing import Any

from agents.agent_base import AgentBase
from config.agent_operating_spec import get_system_prompt
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
        prompt = f"""Conçois un effet visuel pour {game}.
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
}}"""
        return self.run_json_task(
            action="design_vfx",
            prompt=prompt,
            learning_key=effect_name,
            input_summary=f"{game} | {effect_name} | {trigger}",
            output_summary=lambda r: f"{len(r.get('niagara_modules', []))} modules Niagara",
            temperature=0.7,
            max_tokens=2048,
        )

    @trace_agent("vfx_artist")
    def probe_ue58(self) -> dict[str, Any]:
        """Phase 21 / DEC-017 — probe UE5.8 Niagara / VFX capabilities."""
        from skills.skill_ue58 import probe_for_agent

        return probe_for_agent(self.AGENT_NAME)

    @trace_agent("vfx_artist")
    def run_studio_task(self, title: str, description: str) -> dict[str, Any]:
        """DEC-020 — Claude Code agency on local UE project."""
        from skills.skill_gaming_agency import run_studio_task

        return run_studio_task(
            agent_id=self.AGENT_NAME, title=title, description=description
        )
