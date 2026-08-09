"""COO project resolution, context, task logs, and guardrails."""
from __future__ import annotations

from datetime import date, timedelta
from typing import Any

from agents.coo_constants import (
    IRREVERSIBLE_KEYWORDS,
    PROJECT_ALIASES,
    PROJECT_SCOPED_KEYWORDS,
)


class COOProjectMixin:
    """Requires ``self.db`` (SupabaseClient)."""

    def _find_project(self, name: str) -> dict[str, Any] | None:
        """Recherche un projet par nom exact ou alias."""
        normalized = name.strip().lower()
        canonical = PROJECT_ALIASES.get(normalized, name.strip())
        if canonical == "ALNUA":
            return None

        projects = self.db.select("projects")
        for project in projects:
            if project["name"].lower() == canonical.lower():
                return project
            if canonical.lower() in project["name"].lower():
                return project
        return None

    def _resolve_project(
        self,
        project: str | None,
        instruction: str,
    ) -> str | None:
        """Résout le projet depuis le paramètre ou l'instruction."""
        if project:
            found = self._find_project(project)
            return found["name"] if found else project

        lowered = instruction.lower()
        for alias, canonical in sorted(
            PROJECT_ALIASES.items(), key=lambda x: len(x[0]), reverse=True
        ):
            if alias in lowered:
                return canonical
        return None

    def _get_project_context_data(self, project_name: str) -> dict[str, Any]:
        """Agrège l'état complet d'un projet."""
        project = self._find_project(project_name)
        if not project:
            raise ValueError(f"Projet introuvable : {project_name}")

        project_id = project["id"]
        open_tickets = self.db.select(
            "tickets",
            filters={"project_id": project_id, "status": "open"},
            order_by="created_at",
            ascending=False,
            limit=10,
        )
        critical = [t for t in open_tickets if t.get("priority") in ("critical", "high")]
        roadmap = self.db.select(
            "roadmap",
            filters={"project_id": project_id},
            order_by="priority",
            ascending=False,
            limit=5,
        )
        new_feedback = self.db.select(
            "feedback",
            filters={"project_id": project_id, "status": "new"},
            limit=5,
        )
        pending_posts = self.db.select(
            "posts_queue",
            filters={"project_id": project_id, "status": "pending_approval"},
            limit=5,
        )
        week_ago = (date.today() - timedelta(days=7)).isoformat()
        analytics = self.db.select(
            "analytics",
            filters={"project_id": project_id},
            order_by="date",
            ascending=False,
            limit=7,
        )
        analytics = [a for a in analytics if a.get("date", "") >= week_ago]

        return {
            "project": project,
            "open_tickets_count": len(open_tickets),
            "critical_tickets": critical,
            "roadmap_top": roadmap,
            "new_feedback_count": len(new_feedback),
            "pending_posts_count": len(pending_posts),
            "recent_analytics": analytics,
        }

    def _format_project_context(self, project_name: str) -> str:
        data = self._get_project_context_data(project_name)
        p = data["project"]
        lines = [
            f"**{p['name']}** ({p['branch']}) — statut {p['status']}",
            f"Tickets ouverts : {data['open_tickets_count']} "
            f"(critiques/hauts : {len(data['critical_tickets'])})",
            f"Feedback nouveau : {data['new_feedback_count']}",
            f"Posts en attente d'approbation : {data['pending_posts_count']}",
        ]
        if data["critical_tickets"]:
            lines.append("Tickets prioritaires :")
            for t in data["critical_tickets"][:3]:
                lines.append(f"  - {t['title']} [{t['priority']}]")
        if data["roadmap_top"]:
            lines.append("Roadmap (top) :")
            for r in data["roadmap_top"][:3]:
                lines.append(f"  - {r['title']} ({r['status']})")
        if data["recent_analytics"]:
            lines.append("Analytics récents :")
            for a in data["recent_analytics"][:3]:
                lines.append(f"  - {a['metric_name']}: {a['value']} ({a['date']})")
        return "\n".join(lines)

    def _fetch_open_tickets(self, project_name: str) -> list[dict[str, Any]]:
        project = self._find_project(project_name)
        if not project:
            raise ValueError(f"Projet introuvable : {project_name}")
        return self.db.select(
            "tickets",
            filters={"project_id": project["id"], "status": "open"},
            order_by="created_at",
            ascending=False,
        )

    def create_task_log(
        self,
        agent: str,
        action: str,
        input_summary: str,
        output_summary: str,
        project_id: str | None = None,
        status: str = "success",
    ) -> dict[str, Any]:
        """Écrit une entrée dans agent_logs."""
        return self.db.insert(
            "agent_logs",
            {
                "agent_name": agent,
                "action": action,
                "project_id": project_id,
                "input_summary": input_summary[:2000],
                "output_summary": output_summary[:2000],
                "status": status,
            },
        )

    def _check_irreversible(self, instruction: str) -> str | None:
        lowered = instruction.lower()
        if "confirm" in lowered:
            return None
        for keyword in IRREVERSIBLE_KEYWORDS:
            if keyword in lowered:
                return (
                    f"Action irréversible détectée (« {keyword} »). "
                    "Confirme en incluant le mot « confirm » dans ton instruction."
                )
        return None

    def _needs_project_clarification(self, instruction: str) -> bool:
        lowered = instruction.lower()
        if any(alias in lowered for alias in PROJECT_ALIASES):
            return False
        return any(kw in lowered for kw in PROJECT_SCOPED_KEYWORDS)

