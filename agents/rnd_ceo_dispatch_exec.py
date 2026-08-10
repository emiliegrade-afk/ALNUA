"""R&D CEO dispatch — background agent execution and OpenRoom assignment logs."""
from __future__ import annotations

import logging
from typing import Any

from services.rnd_schemas import RndDossierOut

logger = logging.getLogger(__name__)


class RndCeoDispatchExecMixin:
    """Requires ``self.repo`` from the agent init."""

    def _start_dispatch_execution(
        self,
        dossier: RndDossierOut,
        matrix: list[dict[str, Any]],
        package: dict[str, Any],
        project_id: str | None,
        dispatch_payload: dict[str, Any],
    ) -> str | None:
        try:
            from services.rnd_dispatch_executor import start_dispatch_execution_background

            dossier_id = dossier.id

            def _on_complete(result: dict[str, Any]) -> None:
                try:
                    payload = dict(dispatch_payload)
                    payload["execution_status"] = (
                        "completed"
                        if result.get("success_count", 0) > 0
                        else "failed"
                    )
                    payload["execution_result"] = {
                        "success_count": result.get("success_count"),
                        "failure_count": result.get("failure_count"),
                        "total_duration_ms": result.get("total_duration_ms"),
                    }
                    self.repo.update_dossier(dossier_id, {"dispatch_json": payload})
                except Exception as exc:
                    logger.warning("dispatch execution callback failed: %s", exc)

            return start_dispatch_execution_background(
                dossier,
                matrix,
                package,
                project_id,
                self.repo.db,
                on_complete=_on_complete,
            )
        except Exception as exc:
            logger.warning("start dispatch execution failed: %s", exc)
            return None

    def _log_dispatch_assignments(
        self,
        dossier: RndDossierOut,
        matrix: list[dict[str, Any]],
        roadmap_created: list[dict[str, Any]],
        project_id: str | None,
    ) -> None:
        """Create agent_logs so OpenRoom / bureaux show assigned agents as active."""
        roadmap_by_agent = {
            str(item.get("agent_id")): item for item in roadmap_created if item.get("agent_id")
        }
        for row in matrix:
            agent_name = str(row.get("agent_id") or "").strip()
            if not agent_name or agent_name == "coo_agent":
                continue
            deliverables = ", ".join(row.get("deliverables") or [])[:500]
            pole = row.get("pole", agent_name)
            roadmap_item = roadmap_by_agent.get(agent_name)
            task_line = (
                f"[{dossier.title}] {deliverables}"
                if deliverables
                else f"[{dossier.title}] {pole}"
            )
            try:
                self.repo.db.insert(
                    "agent_logs",
                    {
                        "agent_name": agent_name,
                        "action": "rnd_dispatch_assigned",
                        "project_id": project_id,
                        "status": "pending",
                        "input_summary": task_line[:2000],
                        "output_summary": (
                            f"Pôle {pole} — en attente de prise en charge. "
                            f"Roadmap: {roadmap_item.get('title', 'créée') if roadmap_item else 'à planifier'}."
                        )[:2000],
                    },
                )
            except Exception as exc:
                logger.warning("dispatch agent log failed for %s: %s", agent_name, exc)
