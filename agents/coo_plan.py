"""COO plan-executor pipeline and summary trimming."""
from __future__ import annotations

import logging
import re
from typing import Any

from agents.coo_intents import (
    _format_plan_execution_result,
    _is_standalone_rnd_research,
)

logger = logging.getLogger(__name__)


class COOPlanMixin:
    """Requires project helpers + ``create_task_log`` + ``AGENT_NAME``."""

    @staticmethod
    def _trim_summary(text: str, max_lines: int = 5) -> str:
        """Force une réponse courte et actionnable."""
        lines = [ln.strip() for ln in text.strip().splitlines() if ln.strip()]
        # Supprime les lignes trop verbeuses (markdown headers vides, etc.)
        cleaned = []
        for ln in lines:
            ln = re.sub(r"^#+\s*", "", ln)
            ln = ln.strip("*- ")
            if ln:
                cleaned.append(ln)
        return "\n".join(cleaned[:max_lines])

    # ------------------------------------------------------------------
    # Plan executor — exécution réelle multi-agents
    # ------------------------------------------------------------------
    def _execute_plan_pipeline(
        self,
        instruction: str,
        project: str | None,
        telegram_chat_id: int | None,
    ) -> str:
        """Décompose l'objectif en plan COO et exécute les agents (pas de blabla)."""
        import threading

        project_name = self._resolve_project(project, instruction) or "ALNUA"
        if _is_standalone_rnd_research(instruction):
            project_name = "ALNUA"
            context = (
                f"Instruction R&D (hors produit, ne pas créer de tickets sur NUAWAY/Naïa) : "
                f"{instruction[:500]}"
            )
        else:
            context = f"Projet : {project_name}. Instruction Emilie : {instruction[:500]}"

        def _run() -> dict[str, Any]:
            from services.plan_executor import run_coo_plan

            return run_coo_plan(instruction, context)

        if telegram_chat_id is not None:
            ack = (
                "✅ Plan d'action lancé — les agents exécutent les étapes.\n"
                "Je t'envoie le résumé ici dès que c'est terminé."
            )

            def _worker() -> None:
                try:
                    result = _run()
                    summary = _format_plan_execution_result(result)
                    self.create_task_log(
                        self.AGENT_NAME,
                        "plan_execution",
                        instruction,
                        summary[:2000],
                    )
                    from skills.skill_telegram_notify import notify_telegram

                    notify_telegram(summary, chat_id=telegram_chat_id)
                except Exception as exc:
                    logger.exception("COO plan_execution background failed")
                    err = f"❌ Exécution du plan échouée : {exc}"
                    try:
                        self.create_task_log(
                            self.AGENT_NAME,
                            "plan_execution",
                            instruction,
                            err[:500],
                            status="error",
                        )
                    except Exception:
                        pass
                    from skills.skill_telegram_notify import notify_telegram

                    notify_telegram(err, chat_id=telegram_chat_id)

            threading.Thread(
                target=_worker,
                daemon=False,
                name=f"coo-plan-{instruction[:24]}",
            ).start()
            return ack

        try:
            result = _run()
            summary = _format_plan_execution_result(result)
            project_id = None
            if project_name != "ALNUA":
                found = self._find_project(project_name)
                project_id = found["id"] if found else None
            self.create_task_log(
                self.AGENT_NAME,
                "plan_execution",
                instruction,
                summary[:2000],
                project_id,
            )
            return summary
        except Exception as exc:
            logger.exception("COO plan_execution failed")
            err = f"❌ Exécution du plan échouée : {exc}"
            self.create_task_log(
                self.AGENT_NAME,
                "plan_execution",
                instruction,
                err[:500],
                status="error",
            )
            return err
