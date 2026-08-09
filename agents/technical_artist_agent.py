"""Technical Artist Agent — Otto Reindl, optimisation rendu ALNUA Gaming."""
from __future__ import annotations

from typing import Any

from agents.agent_base import AgentBase
from config.agent_operating_spec import get_system_prompt
from skills.skill_langfuse import trace_agent


class TechnicalArtistAgent(AgentBase):
    AGENT_NAME = "technical_artist"
    SYSTEM_PROMPT = get_system_prompt("technical_artist")

    @trace_agent("technical_artist")
    def optimize_render_budget(
        self,
        scene_name: str,
        game: str,
        target_fps: int = 60,
        current_issues: str = "",
    ) -> dict[str, Any]:
        """Analyse le budget de rendu d'une scène et propose des optimisations shader/perf."""
        prompt = f"""Analyse le budget de rendu d'une scène UE5 pour {game}.
Scène : {scene_name}
FPS cible : {target_fps}
Problèmes constatés : {current_issues or 'Aucun signalé — audit préventif'}

Réponds en JSON :
{{
  "scene": "{scene_name}",
  "target_fps": {target_fps},
  "bottlenecks": [{{ "area": "shaders|lighting|draw_calls|textures|particles", "severity": "critical|high|medium|low", "detail": "string" }}],
  "optimizations": [{{ "action": "string", "expected_gain": "string", "risk": "string" }}],
  "shader_notes": "Recommandations shader/matériau",
  "handoff_notes": "Notes pour Nova Fischer (validation gameplay)"
}}"""
        return self.run_json_task(
            action="optimize_render_budget",
            prompt=prompt,
            learning_key=scene_name,
            input_summary=f"{game} | {scene_name} | {target_fps}fps",
            output_summary=lambda r: f"{len(r.get('bottlenecks', []))} goulots identifiés",
            temperature=0.4,
            max_tokens=3072,
        )

    @trace_agent("technical_artist")
    def probe_ue58(self) -> dict[str, Any]:
        """Phase 21 / DEC-017 — probe UE5.8 render capabilities."""
        from skills.skill_ue58 import probe_for_agent

        return probe_for_agent(self.AGENT_NAME)
