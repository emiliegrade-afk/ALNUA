"""Brainstorm agent — legacy one-shot JSON brainstorm and roadmap helpers."""
from __future__ import annotations

from typing import Any

from agents.base import log_agent_action, parse_json_response


class BrainstormLegacyMixin:
    """Requires ``self.db``, ``self.AGENT_NAME``, ``self._complete``."""

    def brainstorm(
        self,
        project_id: str,
        topic: str,
        context_notes: str = "",
    ) -> dict[str, Any]:
        project = self.db.select("projects", filters={"id": project_id})
        if not project:
            raise ValueError(f"Project {project_id} not found")

        roadmap = self.db.select("roadmap", filters={"project_id": project_id}, limit=10)
        recent_feedback = self.db.select(
            "feedback",
            filters={"project_id": project_id},
            order_by="created_at",
            ascending=False,
            limit=10,
        )

        user_prompt = f"""Projet : {project[0]['name']} — {project[0]['description']}
Branche : {project[0]['branch']}
Sujet : {topic}
Notes : {context_notes}
Roadmap actuelle : {roadmap}
Feedback récent : {recent_feedback}

Génère 5 à 8 idées originales."""

        try:
            raw = self._complete(user_prompt, temperature=0.9)
            result = parse_json_response(raw)
            log_agent_action(
                self.db,
                self.AGENT_NAME,
                "brainstorm",
                input_summary=f"topic={topic}",
                output_summary=f"{len(result.get('ideas', []))} idées",
                status="success",
                project_id=project_id,
            )
            return result
        except Exception as exc:
            log_agent_action(
                self.db,
                self.AGENT_NAME,
                "brainstorm",
                input_summary=f"topic={topic}",
                output_summary=str(exc),
                status="error",
                project_id=project_id,
            )
            raise

    def add_top_idea_to_roadmap(
        self,
        project_id: str,
        idea: dict[str, Any],
        phase: str = "backlog",
    ) -> dict[str, Any]:
        impact_map = {"low": "low", "medium": "medium", "high": "high"}
        priority = impact_map.get(idea.get("impact", "medium"), "medium")
        return self.db.insert(
            "roadmap",
            {
                "project_id": project_id,
                "title": idea["title"],
                "description": idea.get("description", ""),
                "phase": phase,
                "priority": priority,
                "status": "idea",
            },
        )
