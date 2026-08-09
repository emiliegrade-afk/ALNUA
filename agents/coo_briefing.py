"""COO daily briefing aggregation."""
from __future__ import annotations

import logging
from datetime import date
from typing import Any

from agents.coo_constants import BRANCH_LABELS

logger = logging.getLogger(__name__)


class COOBriefingMixin:
    """Requires ``self.db`` and ``_get_project_context_data``."""

    def get_daily_briefing(self) -> dict[str, Any]:
        """Résumé structuré de tous les projets."""
        projects = self.db.select("projects", order_by="branch")
        per_project: list[dict[str, Any]] = []
        summary_lines: list[str] = [f"📋 Briefing ALNUA — {date.today().isoformat()}"]

        total_critical = 0
        total_pending_posts = 0
        total_new_feedback = 0
        urgent_lines: list[str] = []
        branch_ctx: dict[str, list[dict[str, Any]]] = {
            "app": [],
            "gaming": [],
            "robotics": [],
        }

        for project in projects:
            try:
                ctx = self._get_project_context_data(project["name"])
            except Exception as exc:
                logger.warning("Briefing partiel pour %s : %s", project["name"], exc)
                continue

            critical = len(ctx["critical_tickets"])
            pending = ctx["pending_posts_count"]
            feedback = ctx["new_feedback_count"]
            total_critical += critical
            total_pending_posts += pending
            total_new_feedback += feedback

            per_project.append(ctx)
            branch_key = project.get("branch", "other")
            if branch_key in branch_ctx:
                branch_ctx[branch_key].append({"project": project, "ctx": ctx})

            for ticket in ctx["critical_tickets"]:
                urgent_lines.append(
                    f"• [{project['name']}] {ticket['title']} ({ticket['priority']})"
                )

            summary_lines.append(
                f"• {project['name']} ({project.get('status', '?')}) : "
                f"{ctx['open_tickets_count']} tickets, "
                f"{critical} prioritaires, "
                f"{feedback} feedbacks, "
                f"{pending} posts en attente"
            )

        summary_lines.append("")
        summary_lines.append("🏢 Branches :")
        for branch_key in ("app", "gaming", "robotics"):
            label = BRANCH_LABELS[branch_key]
            entries = branch_ctx[branch_key]
            if not entries:
                summary_lines.append(f"• {label} : aucun projet actif")
                continue
            open_tickets = sum(e["ctx"]["open_tickets_count"] for e in entries)
            critical_count = sum(len(e["ctx"]["critical_tickets"]) for e in entries)
            names = ", ".join(e["project"]["name"] for e in entries)
            summary_lines.append(
                f"• {label} : {len(entries)} projet(s), "
                f"{open_tickets} tickets, {critical_count} urgent(s) — {names}"
            )

        if urgent_lines:
            summary_lines.append("")
            summary_lines.append("⚡ Tâches urgentes :")
            summary_lines.extend(urgent_lines[:10])
            if len(urgent_lines) > 10:
                summary_lines.append(f"… et {len(urgent_lines) - 10} autre(s)")

        if total_critical:
            summary_lines.append(f"⚠️ {total_critical} ticket(s) critique(s)/haut(s) au total.")
        if total_pending_posts:
            summary_lines.append(f"📣 {total_pending_posts} post(s) à valider.")
        if total_new_feedback:
            summary_lines.append(f"💬 {total_new_feedback} feedback(s) non traité(s).")

        from skills.skill_error_journal import get_open_errors_summary

        errors_summary = get_open_errors_summary()
        if not errors_summary.startswith("[OK]"):
            summary_lines.append("")
            summary_lines.append("🔴 Journal d'erreurs agents :")
            summary_lines.append(errors_summary)

        summary_lines.append("→ Dis-moi sur quoi tu veux te concentrer aujourd'hui.")

        return {
            "date": date.today().isoformat(),
            "projects": per_project,
            "summary": "\n".join(summary_lines),
        }

    def run_daily_briefing(self) -> str:
        """Compatibilité API / Discord — retourne le briefing formaté."""
        return self.get_daily_briefing()["summary"]
