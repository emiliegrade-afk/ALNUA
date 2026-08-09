"""COO delegation helpers to PM / QA / Content / Brainstorm / Spec."""
from __future__ import annotations

from typing import Any


class COODelegatesMixin:
    """Requires ``self.db``, ``self.verbose``, ``_find_project``, ``create_task_log``."""

    def _require_project(self, project_name: str) -> dict[str, Any]:
        project = self._find_project(project_name)
        if not project:
            raise ValueError(f"Projet introuvable : {project_name}")
        return project

    def _delegate_pm(self, project_name: str, instruction: str = "") -> str:
        from agents.pm_agent import PMAgent

        project = self._require_project(project_name)
        pm = PMAgent(self.db, verbose=self.verbose)
        task = instruction.strip() or f"Triage roadmap et tickets pour {project_name}"
        summary = pm.handle_instruction(task, project["id"])
        self.create_task_log(
            "pm_agent", "handle_instruction", f"{project_name}: {task}", summary, project["id"]
        )
        return summary

    def _delegate_qa(self, project_name: str) -> str:
        from agents.qa_agent import QAAgent

        project = self._require_project(project_name)
        result = QAAgent(self.db).analyze_feedback_batch(project["id"])
        summary = result.get("summary", "Analyse QA terminée.")
        self.create_task_log(
            "qa_agent", "analyze_feedback", project_name, summary, project["id"]
        )
        return summary

    def _delegate_content(self, project_name: str) -> str:
        from agents.content_agent import ContentAgent

        project = self._require_project(project_name)
        posts = ContentAgent(self.db).generate_from_dev_logs(project["id"])
        summary = f"{len(posts)} post(s) généré(s), en attente d'approbation."
        self.create_task_log(
            "content_agent", "generate_from_dev_logs", project_name, summary, project["id"]
        )
        return summary

    def _delegate_brainstorm(self, project_name: str, topic: str) -> str:
        from agents.brainstorm_agent import BrainstormAgent

        project = self._require_project(project_name)
        result = BrainstormAgent(self.db).brainstorm(project["id"], topic)
        ideas = result.get("ideas", [])
        titles = ", ".join(i["title"] for i in ideas[:3]) or "aucune idée"
        summary = f"{len(ideas)} idée(s) : {titles}"
        self.create_task_log(
            "brainstorm_agent", "brainstorm", f"{project_name}: {topic}", summary, project["id"]
        )
        return summary

    def _delegate_spec(self, ticket_id: str) -> str:
        from agents.spec_agent import SpecAgent

        ticket = SpecAgent(self.db).generate_cursor_prompt(ticket_id)
        summary = f"Prompt Cursor généré pour « {ticket.get('title', ticket_id)} »."
        self.create_task_log(
            "spec_agent",
            "generate_cursor_prompt",
            ticket_id,
            summary,
            ticket.get("project_id"),
        )
        return summary
