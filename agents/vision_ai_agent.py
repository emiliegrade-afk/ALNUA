"""Vision IA Agent — Sana Okoye, perception embarquée ALNUA Robotique."""
from __future__ import annotations

from typing import Any

from agents.agent_base import AgentBase
from config.agent_operating_spec import get_system_prompt
from skills.skill_langfuse import trace_agent


class VisionAiAgent(AgentBase):
    AGENT_NAME = "vision_ai"
    SYSTEM_PROMPT = get_system_prompt("vision_ai")

    @trace_agent("vision_ai")
    def design_detection_pipeline(
        self,
        task_name: str,
        target_objects: str = "",
        constraints: str = "",
    ) -> dict[str, Any]:
        """Conçoit un pipeline de détection/perception adapté aux contraintes Pi d'Eve."""
        prompt = f"""Conçois un pipeline de vision par ordinateur pour Eve robot.
Tâche : {task_name}
Objets/cibles à détecter : {target_objects or 'À définir'}
Contraintes : {constraints or 'Raspberry Pi + caméra DepthAI, latence temps réel'}

Réponds en JSON :
{{
  "task": "{task_name}",
  "targets": ["{target_objects}"],
  "pipeline_steps": [{{ "step": "string", "detail": "string" }}],
  "model_choice": "Modèle/approche recommandée et pourquoi",
  "latency_estimate_ms": 0,
  "failure_modes": ["Cas où la détection risque d'échouer"],
  "handoff_notes": "Notes pour Zara Singh (embedded_dev) — intégration réactive"
}}"""
        return self.run_json_task(
            action="design_detection_pipeline",
            prompt=prompt,
            learning_key=task_name,
            input_summary=f"{task_name} | {target_objects}",
            output_summary=lambda r: f"{len(r.get('pipeline_steps', []))} étapes de pipeline",
            temperature=0.4,
            max_tokens=2048,
        )
