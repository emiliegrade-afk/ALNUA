"""R&D CEO agent — COO dispatch, roadmap creation, agent execution kickoff."""
from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any

from agents.rnd_social_agent import ensure_project_for_dossier
from agents.rnd_ceo_errors import (
    DispatchNotAllowedError,
    normalize_priority_label,
    roadmap_priority_values,
)
from services.rnd_ceo_package import build_dispatch_matrix
from agents.rnd_ceo_dispatch_exec import RndCeoDispatchExecMixin

logger = logging.getLogger(__name__)


class RndCeoDispatchMixin(RndCeoDispatchExecMixin):
    """Requires helper mixin for dossier/package loads."""

    def dispatch_to_coo(
        self,
        dossier_id: str,
        *,
        actor: str = "emilie",
    ) -> dict[str, Any]:
        dossier = self._require_dossier(dossier_id)
        if dossier.ceo_status != "approved":
            raise DispatchNotAllowedError(
                "Dispatch COO disponible uniquement après validation CEO (approved)."
            )
        if self._load_dispatch_status(dossier_id) == "dispatched":
            existing = self._load_dispatch_json(dossier_id) or {}
            if existing.get("roadmap_items"):
                exec_status = existing.get("execution_status")
                run_id = existing.get("execution_run_id")
                if exec_status not in ("running", "completed"):
                    package = self._load_package_json(dossier_id) or {}
                    matrix = (
                        existing.get("matrix")
                        or package.get("dispatch_matrix")
                        or build_dispatch_matrix(dossier)
                    )
                    project_id = existing.get("project_id") or ensure_project_for_dossier(
                        dossier, self.repo.db
                    )
                    run_id = self._start_dispatch_execution(
                        dossier, matrix, package, project_id, existing
                    )
                    if run_id:
                        existing = dict(existing)
                        existing["execution_run_id"] = run_id
                        existing["execution_status"] = "running"
                        self.repo.update_dossier(
                            dossier_id,
                            {"dispatch_json": existing},
                        )
                return {
                    "message": (
                        "Dispatch déjà effectué — exécution agents "
                        + ("en cours." if exec_status == "running" or run_id else "relancée.")
                    ),
                    "dispatch": existing,
                    "already_dispatched": True,
                    "execution_run_id": run_id,
                }
            logger.info("Re-dispatch: dispatched flag set but no roadmap items for %s", dossier_id)

        package = self._load_package_json(dossier_id) or {}
        matrix = package.get("dispatch_matrix") or build_dispatch_matrix(dossier)
        project_id = ensure_project_for_dossier(dossier, self.repo.db)

        slug = dossier.slug or dossier.id
        workspace_path_str: str = ""
        try:
            from config.paths import get_alnua_workspace
            from services.rnd_workspace import init_project_workspace

            init_project_workspace(slug)
            workspace_path_str = str(get_alnua_workspace())
            self.repo.update_dossier(dossier_id, {"workspace_path": workspace_path_str})
            if project_id:
                try:
                    self.repo.db.update(
                        "projects",
                        project_id,
                        {"workspace_path": workspace_path_str},
                    )
                except Exception as proj_exc:
                    logger.warning("projects.workspace_path update failed: %s", proj_exc)
        except Exception as _wp_exc:
            logger.warning("init_project_workspace failed for %s: %s", slug, _wp_exc)

        roadmap_created: list[dict[str, Any]] = []
        for row in matrix:
            priority_label = normalize_priority_label(row.get("priority", "medium"))
            phase = row.get("phase", "conception")
            title = row.get("roadmap_title", row["pole"])[:200]
            desc = f"{row.get('description', '')}\n\nPhase: {phase}."[:2000]
            item_row = None
            last_exc: Exception | None = None
            for priority in roadmap_priority_values(priority_label):
                for extra in (
                    {"phase": phase, "rnd_dossier_id": dossier_id},
                    {"rnd_dossier_id": dossier_id},
                    {},
                ):
                    payload = {
                        "project_id": project_id,
                        "title": title,
                        "description": desc,
                        "status": "planned",
                        "priority": priority,
                        **extra,
                    }
                    try:
                        item = self.repo.db.insert("roadmap", payload)
                        item_row = item[0] if isinstance(item, list) else item
                        break
                    except Exception as exc:
                        last_exc = exc
                if item_row:
                    break
            if item_row:
                roadmap_created.append(
                    {
                        "id": str(item_row["id"]),
                        "title": item_row.get("title"),
                        "pole": row.get("pole"),
                        "agent_id": row.get("agent_id"),
                    }
                )
            elif last_exc:
                logger.warning(
                    "dispatch roadmap insert failed for %s: %s",
                    row.get("pole"),
                    last_exc,
                )

        dispatch_payload = {
            "matrix": matrix,
            "roadmap_items": roadmap_created,
            "dispatched_at": datetime.now(timezone.utc).isoformat(),
            "project_id": project_id,
            "workspace_path": workspace_path_str,
        }

        self.repo.update_dossier(
            dossier_id,
            {
                "dispatch_json": dispatch_payload,
                "dispatch_status": "dispatched",
                "status": "in_conception",
            },
        )

        idea_row = self.repo.get_idea_db_row(dossier.idea_id)
        if idea_row and idea_row.get("id"):
            self.repo.db.update(
                "rnd_ideas",
                idea_row["id"],
                {"lifecycle_status": "in_conception"},
            )

        self._log_dispatch_assignments(dossier, matrix, roadmap_created, project_id)

        try:
            self.repo.db.insert(
                "agent_logs",
                {
                    "agent_name": "coo_agent",
                    "action": "rnd_dispatch_brief",
                    "project_id": project_id,
                    "status": "pending",
                    "input_summary": (
                        f"Nouveau projet validé CEO : {dossier.title}. "
                        f"{len(roadmap_created)} tâches roadmap créées. "
                        f"Orchestre les pôles — /roadmap?project_id={project_id}"
                    ),
                    "output_summary": str(dispatch_payload)[:4000],
                },
            )
        except Exception as exc:
            logger.warning("coo brief log failed: %s", exc)

        self.repo.log_event(
            dossier_id,
            "coo_dispatched",
            actor,
            {
                "roadmap_count": len(roadmap_created),
                "project_id": project_id,
            },
        )

        package = self._load_package_json(dossier_id) or {}
        run_id = self._start_dispatch_execution(
            dossier, matrix, package, project_id, dispatch_payload
        )
        if run_id:
            dispatch_payload["execution_run_id"] = run_id
            dispatch_payload["execution_status"] = "running"
            self.repo.update_dossier(
                dossier_id,
                {"dispatch_json": dispatch_payload},
            )

        return {
            "message": (
                f"Dispatch COO effectué — {len(roadmap_created)} entrées roadmap. "
                "Les agents exécutent les livrables (OpenRoom)."
            ),
            "dispatch": dispatch_payload,
            "roadmap_items": roadmap_created,
            "project_id": project_id,
            "execution_run_id": run_id,
            "workspace_path": workspace_path_str,
        }

    def promote_idea_to_department(self, idea_id: str, *, actor: str = "emilie") -> dict[str, Any]:
        """Incubateur — glisser une carte vers Département = approbation CEO explicite."""
        idea = self.repo.get_idea_by_id(idea_id)
        if not idea:
            raise ValueError(f"Idée introuvable : {idea_id}")

        if idea.dossier_id:
            dossier_id = str(idea.dossier_id)
        else:
            from agents.rnd_dossier_agent import promote_idea_to_dossier as _promote

            created = _promote(idea_id, actor=actor, enrich=False)
            dossier_id = created["dossier"]["id"]

        self.generate_package(dossier_id, actor=actor)
        self.record_ceo_decision(dossier_id, ceo_status="approved", actor=actor)
        dispatch_result = self.dispatch_to_coo(dossier_id, actor=actor)

        return {"dossier_id": dossier_id, "dispatch": dispatch_result}

    def kickoff_execution(self, dossier_id: str) -> dict[str, Any]:
        """Re-lance l'exécution agents pour un dossier déjà dispatché."""
        dossier = self._require_dossier(dossier_id)
        if dossier.ceo_status != "approved":
            raise DispatchNotAllowedError("Validation CEO requise.")
        dispatch = self._load_dispatch_json(dossier_id) or {}
        matrix = dispatch.get("matrix") or []
        if not matrix:
            package = self._load_package_json(dossier_id) or {}
            matrix = package.get("dispatch_matrix") or build_dispatch_matrix(dossier)
        package = self._load_package_json(dossier_id) or {}
        project_id = dispatch.get("project_id")
        if not project_id:
            project_id = ensure_project_for_dossier(dossier, self.repo.db)
        run_id = self._start_dispatch_execution(
            dossier, matrix, package, project_id, dispatch
        )
        return {
            "message": "Exécution agents lancée — suis l'OpenRoom.",
            "execution_run_id": run_id,
        }
