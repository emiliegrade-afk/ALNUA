"""Technical Artist Agent — Otto Reindl, optimisation rendu ALNUA Gaming."""

from __future__ import annotations

from agents.agent_base import AgentBase

from typing import Any

from agents.base import log_agent_action, parse_json_response
from config.agent_operating_spec import get_system_prompt
from skills.skill_agent_learning import inject_learning_context, record_task_learning
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
        prompt = inject_learning_context(
            f"""Analyse le budget de rendu d'une scène UE5 pour {game}.
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
}}""",
            self.AGENT_NAME, scene_name,
        )
        raw = self._complete(prompt, temperature=0.4, max_tokens=3072)
        result = parse_json_response(raw)
        log_agent_action(
            self.db, self.AGENT_NAME, "optimize_render_budget",
            input_summary=f"{game} | {scene_name} | {target_fps}fps",
            output_summary=f"{len(result.get('bottlenecks', []))} goulots identifiés",
        )
        try:
            record_task_learning(self.AGENT_NAME, "optimize_render_budget", str(result)[:400], success=True)
        except Exception:
            pass
        return result
