"""
rnd_ceo_agent.py — Package CEO, validation Emilie, dispatch COO (phase 6).
"""

from __future__ import annotations

import logging
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from agents.base import LLMClient
from config.agent_operating_spec import get_system_prompt
from agents.rnd_social_agent import ensure_project_for_dossier
from services.rnd_ceo_package import (
    CEO_PACKAGE_OUTLINE,
    build_ceo_package_json,
    build_ceo_package_md,
    build_dispatch_matrix,
)
from services.rnd_repository import get_rnd_repository
from services.rnd_schemas import RndDossierOut

logger = logging.getLogger(__name__)

PACKAGE_ELIGIBLE_STATUSES = frozenset({
    "partial_validated",
    "ready_for_ceo",
    "ceo_approved",
    "ceo_rejected",
    "in_conception",
})


def _ceo_package_eligible(dossier: RndDossierOut) -> bool:
    """Package CEO si comité terminé (CR) ou statut pipeline avancé."""
    if dossier.status in PACKAGE_ELIGIBLE_STATUSES:
        return True
    cr = (dossier.committee_report_md or "").strip()
    return len(cr) >= 40

COMMITTEE_REPORT_TEMPLATE = """Rédige un **compte-rendu de clôture comité R&D** markdown pour Emilie (CEO).
Ne résume PAS à l'excès : chaque sujet abordé en réunion doit apparaître.

## Synthèse chronologique des échanges
[Reprendre TOUS les sujets : coûts, pricing, MVP, objections, arbitrages, questions Emilie]

## Chiffres & hypothèses évoqués en réunion
| Élément | Valeur / hypothèse | Source (qui) |
|---------|-------------------|--------------|

## Amendements & demandes Emilie
[Liste à puces — reformulations, réductions coût, périmètre, priorités]

## Décisions actées
[Liste à puces — ce qui a été tranché]

## Sections validées / à revoir
| Section | Statut | Commentaire comité |
|---------|--------|-------------------|

## Actions ouvertes
- [ ] ...

## Risques ouverts
- ...

## Recommandation GO / MAYBE / NO pour le CEO
**Verdict :** GO|MAYBE|NO
[2-4 phrases factuelles]

---
*CR généré automatiquement — ALNUA Hub R&D*
"""


class CeoPackageNotReadyError(ValueError):
    """Dossier not ready for CEO package generation."""


class CeoDecisionError(ValueError):
    """Invalid CEO decision state."""


class DispatchNotAllowedError(ValueError):
    """Dispatch blocked — CEO approval required."""


_PRIORITY_TEXT_TO_INT = {
    "critical": 9,
    "high": 7,
    "medium": 5,
    "low": 2,
}


def _roadmap_priority_values(label: str) -> list[Any]:
    """Support text (v2) and integer (legacy) roadmap.priority columns."""
    text = label if label in _PRIORITY_TEXT_TO_INT else "medium"
    return [text, _PRIORITY_TEXT_TO_INT[text]]


class RndCeoAgent:
    AGENT_NAME = "rnd_ceo_agent"

    def __init__(self) -> None:
        self.repo = get_rnd_repository()
        self.llm = LLMClient()
        self.data_root = Path(
            os.getenv("HUB_REPO_PATH", "C:/Dev/ALUNA_HUB")
        ) / "data" / "rnd_dossiers"

    def get_package(self, dossier_id: str) -> dict[str, Any]:
        dossier = self._require_dossier(dossier_id)
        row_pkg = dossier.ceo_package_json or self._load_package_json(dossier_id)
        committee_report = dossier.committee_report_md or self._load_committee_report(dossier_id)
        dispatch_status = dossier.dispatch_status or self._load_dispatch_status(dossier_id)
        dispatch_json = dossier.dispatch_json or self._load_dispatch_json(dossier_id)
        return {
            "dossier_id": dossier.id,
            "dossier_status": dossier.status,
            "ceo_status": dossier.ceo_status,
            "ceo_note": dossier.ceo_note,
            "dispatch_status": dispatch_status,
            "committee_report_md": committee_report,
            "package": row_pkg,
            "dispatch": dispatch_json,
            "markdown": (row_pkg or {}).get("markdown") or dossier.one_pager_md,
            "can_generate": _ceo_package_eligible(dossier),
            "can_decide": dossier.status == "ready_for_ceo"
            and bool(row_pkg)
            and dossier.ceo_status == "pending",
            "can_dispatch": dossier.ceo_status == "approved"
            and dispatch_status != "dispatched",
        }

    def list_pending_dossiers(self, *, limit: int = 20) -> list[dict[str, Any]]:
        """Dossiers with CEO package generated, awaiting Emilie's decision."""
        queue = self.list_ceo_queue(limit=limit)
        return queue["to_validate"]

    def list_ceo_queue(self, *, limit: int = 20) -> dict[str, list[dict[str, Any]]]:
        """CEO bureau queue: ready to decide vs needs package generation."""
        if not self.repo._use_db:
            return {"to_validate": [], "to_prepare": []}
        try:
            rows = self.repo.db.select(
                "rnd_dossiers",
                order_by="updated_at",
                ascending=False,
                limit=max(limit * 4, 40),
            )
        except Exception as exc:
            logger.warning("list_ceo_queue failed: %s", exc)
            return {"to_validate": [], "to_prepare": []}

        to_validate: list[dict[str, Any]] = []
        to_prepare: list[dict[str, Any]] = []

        for row in rows:
            if row.get("ceo_status") != "pending":
                continue
            if row.get("status") in ("ceo_approved", "ceo_rejected", "archived"):
                continue

            pkg = row.get("ceo_package_json")
            has_cr = bool((row.get("committee_report_md") or "").strip())
            status = row.get("status", "draft")
            item = self._ceo_queue_item(row, pkg)

            if pkg and status in ("ready_for_ceo", "partial_validated"):
                to_validate.append(item)
            elif not pkg and (
                status in ("partial_validated", "ready_for_ceo")
                or (status == "draft" and has_cr)
                or (status == "committee_active" and has_cr)
            ):
                item["needs_action"] = "generate_package"
                to_prepare.append(item)

            if len(to_validate) >= limit and len(to_prepare) >= limit:
                break

        return {
            "to_validate": to_validate[:limit],
            "to_prepare": to_prepare[:limit],
        }

    @staticmethod
    def _ceo_queue_item(row: dict[str, Any], pkg: Any) -> dict[str, Any]:
        recommendation = None
        branch = None
        if isinstance(pkg, dict):
            recommendation = pkg.get("recommendation")
            branch = pkg.get("branch")
        return {
            "id": str(row["id"]),
            "slug": row.get("slug"),
            "title": row.get("title"),
            "domain": row.get("domain", "autre"),
            "branch": branch or row.get("branch"),
            "status": row.get("status"),
            "ceo_status": row.get("ceo_status", "pending"),
            "recommendation": recommendation,
            "updated_at": row.get("updated_at"),
            "can_decide": bool(pkg) and row.get("status") == "ready_for_ceo",
            "has_committee_report": bool((row.get("committee_report_md") or "").strip()),
        }

    def generate_package(
        self,
        dossier_id: str,
        *,
        actor: str = "rnd_ceo_agent",
        force: bool = False,
    ) -> dict[str, Any]:
        dossier = self._require_dossier(dossier_id)
        if not _ceo_package_eligible(dossier):
            raise CeoPackageNotReadyError(
                f"Package CEO disponible après comité R&D "
                f"(statut actuel : {dossier.status})."
            )

        existing = self._load_package_json(dossier_id)
        if existing and not force:
            return {
                "package": existing,
                "message": "Package CEO déjà généré — utilise force=true pour regénérer.",
                "regenerated": False,
            }

        committee_report, committee_transcript = self._resolve_committee_materials(
            dossier_id, dossier
        )

        portfolio_rows = self._load_portfolio_rows()

        markdown = build_ceo_package_md(
            dossier,
            committee_report_md=committee_report,
            committee_transcript_md=committee_transcript,
            portfolio_rows=portfolio_rows,
        )
        markdown = self._polish_ceo_package_md(
            dossier,
            markdown,
            committee_report,
            committee_transcript,
        )
        package_json = build_ceo_package_json(
            dossier,
            committee_report_md=committee_report,
            committee_transcript_md=committee_transcript,
            markdown=markdown,
            portfolio_rows=portfolio_rows,
        )

        local_path = self._write_local_package(dossier.slug, markdown)
        dispatch_matrix = package_json["dispatch_matrix"]

        self.repo.update_dossier(
            dossier_id,
            {
                "ceo_package_json": package_json,
                "committee_report_md": committee_report,
                "one_pager_md": markdown,
                "dispatch_json": {"matrix": dispatch_matrix, "roadmap_items": []},
                "dispatch_status": "ready",
                "status": "ready_for_ceo" if dossier.status != "ceo_approved" else dossier.status,
            },
        )

        idea_row = self.repo.get_idea_db_row(dossier.idea_id)
        if idea_row and idea_row.get("id"):
            self.repo.db.update(
                "rnd_ideas",
                idea_row["id"],
                {"lifecycle_status": "ceo_review"},
            )

        self.repo.log_event(
            dossier_id,
            "ceo_package_generated",
            actor,
            {
                "branch": package_json.get("branch"),
                "recommendation": package_json.get("recommendation"),
                "local_path": str(local_path),
            },
        )

        return {
            "package": package_json,
            "markdown": markdown,
            "local_path": str(local_path),
            "message": "Dossier CEO généré — prêt pour validation Emilie.",
            "regenerated": bool(existing),
        }

    def record_ceo_decision(
        self,
        dossier_id: str,
        *,
        ceo_status: str,
        ceo_note: str | None = None,
        actor: str = "emilie",
    ) -> dict[str, Any]:
        dossier = self._require_dossier(dossier_id)
        if ceo_status not in ("approved", "rejected", "pivot_requested"):
            raise CeoDecisionError(f"ceo_status invalide : {ceo_status}")

        if not self._load_package_json(dossier_id):
            raise CeoDecisionError(
                "Génère d'abord le package CEO avant de valider."
            )

        status_map = {
            "approved": "ceo_approved",
            "rejected": "ceo_rejected",
            "pivot_requested": "partial_validated",
        }
        new_status = status_map[ceo_status]
        decided_at = datetime.now(timezone.utc).isoformat()

        self.repo.update_dossier(
            dossier_id,
            {
                "ceo_status": ceo_status,
                "ceo_note": ceo_note,
                "ceo_decided_at": decided_at,
                "status": new_status,
            },
        )

        idea_row = self.repo.get_idea_db_row(dossier.idea_id)
        if idea_row and idea_row.get("id"):
            lifecycle = {
                "approved": "approved",
                "rejected": "rejected",
                "pivot_requested": "sections_review",
            }[ceo_status]
            self.repo.db.update(
                "rnd_ideas",
                idea_row["id"],
                {"lifecycle_status": lifecycle},
            )

        # Update decision section
        rec = {"approved": "GO", "rejected": "NO", "pivot_requested": "MAYBE"}[ceo_status]
        decision_md = (
            f"## Décision CEO\n\n"
            f"**Verdict :** {rec}\n\n"
            f"**Statut :** {ceo_status}\n\n"
            f"{ceo_note or '_Sans note._'}\n\n"
            f"*Décision le {decided_at[:10]}*"
        )
        self.repo.update_section_content(
            dossier_id,
            "decision",
            decision_md,
            status="validated",
        )

        self.repo.log_event(
            dossier_id,
            "ceo_decision",
            actor,
            {"ceo_status": ceo_status, "ceo_note": ceo_note},
        )

        dispatch_result: dict[str, Any] | None = None
        dispatch_error: str | None = None
        if ceo_status == "approved" and self._load_dispatch_status(dossier_id) != "dispatched":
            try:
                dispatch_result = self.dispatch_to_coo(dossier_id, actor=actor)
            except Exception as exc:
                dispatch_error = str(exc)
                logger.warning("auto dispatch on CEO approve failed: %s", exc)

        if ceo_status == "approved" and dispatch_result:
            n = len(dispatch_result.get("roadmap_items") or [])
            message = (
                f"Projet approuvé — dispatch COO effectué ({n} tâches, agents notifiés)."
            )
        elif ceo_status == "approved" and self._load_dispatch_status(dossier_id) == "dispatched":
            message = "Projet approuvé — dispatch COO déjà en place."
        elif ceo_status == "approved" and dispatch_error:
            message = (
                "Projet approuvé — dispatch COO à relancer manuellement "
                f"({dispatch_error[:120]})."
            )
        elif ceo_status == "approved":
            message = "Projet approuvé — lance le dispatch COO."
        else:
            message = "Décision enregistrée."

        return {
            "dossier_status": new_status,
            "ceo_status": ceo_status,
            "ceo_note": ceo_note,
            "dispatch": dispatch_result,
            "dispatch_error": dispatch_error,
            "message": message,
        }

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

        # --- Phase 9 : Init workspace disque (Option A : ALNUA/{pole}/{slug}/) ---
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
            priority_label = row.get("priority", "medium")
            if priority_label not in _PRIORITY_TEXT_TO_INT:
                priority_label = "medium"
            phase = row.get("phase", "conception")
            title = row.get("roadmap_title", row["pole"])[:200]
            desc = f"{row.get('description', '')}\n\nPhase: {phase}."[:2000]
            item_row = None
            last_exc: Exception | None = None
            for priority in _roadmap_priority_values(priority_label):
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

        # Notify assigned agents — OpenRoom picks pending logs (< 15 min)
        self._log_dispatch_assignments(dossier, matrix, roadmap_created, project_id)

        # Brief COO via agent_logs for dashboard pickup
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
        """Incubateur (Phase 24, ROADMAP.md) — glisser une carte vers la
        colonne Département est un geste d'approbation CEO explicite.

        Enchaîne : dossier (créé si l'idée n'en a pas encore) → package CEO
        (généré si absent et éligible) → décision approuvée → dispatch COO.
        Ne fabrique jamais une approbation : si le dossier n'est pas encore
        éligible (pas de rapport comité), `generate_package` lève
        `CeoPackageNotReadyError` et cette méthode la laisse remonter telle
        quelle — le geste de glisser est refusé plutôt que simulé.
        """
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

    def generate_committee_report(
        self,
        dossier_id: str,
        history: list[dict[str, Any]],
        *,
        dossier: RndDossierOut | None = None,
    ) -> str:
        dossier = dossier or self._require_dossier(dossier_id)
        return self._generate_committee_report_llm(dossier, history)

    def _resolve_committee_materials(
        self,
        dossier_id: str,
        dossier: RndDossierOut,
    ) -> tuple[str, str]:
        """Reload transcript from DB and refresh CR before CEO package."""
        from services.rnd_committee import (
            format_committee_transcript_md,
            get_committee_repository,
        )

        stored_report = self._load_committee_report(dossier_id) or ""
        repo = get_committee_repository()
        history, session = repo.load_closed_session_history(dossier_id)
        if not history:
            active = repo.get_active_session(dossier_id)
            if active:
                history = repo.list_messages(active["session_id"], limit=300)
                session = active
        transcript = format_committee_transcript_md(
            history,
            session_title=(session or {}).get("title"),
        )

        if history:
            fresh_report = self._generate_committee_report_llm(dossier, history)
            committee_report = (
                fresh_report
                if len(fresh_report) >= len(stored_report) * 0.6
                else (stored_report or fresh_report)
            )
        elif stored_report:
            committee_report = stored_report
        else:
            committee_report = self._generate_committee_report_from_dossier(dossier)

        return committee_report.strip(), transcript

    def _polish_ceo_package_md(
        self,
        dossier: RndDossierOut,
        skeleton_md: str,
        committee_report: str | None,
        committee_transcript: str | None = None,
    ) -> str:
        """LLM pass — intègre réunion comité dans le dossier CEO."""
        if not self._should_use_llm():
            return skeleton_md
        user = (
            f"Projet : {dossier.title} ({dossier.domain}, branche {dossier.branch or 'app'})\n\n"
            f"{CEO_PACKAGE_OUTLINE}\n\n"
            "CONSIGNE CRITIQUE : chaque décision, chiffre, objection et demande d'Emilie "
            "mentionnée en réunion DOIT apparaître dans la section pertinente (1-6). "
            "Ne pas omettre de sujet discuté.\n\n"
            f"Transcript réunion comité :\n{(committee_transcript or '')[:20000]}\n\n"
            f"Compte-rendu structuré :\n{(committee_report or '')[:8000]}\n\n"
            f"Brouillon dossier à réécrire au propre :\n{skeleton_md[:12000]}"
        )
        try:
            polished = self.llm.complete(
                get_system_prompt("rnd_ceo_package"),
                user,
                agent_id=self.AGENT_NAME,
                temperature=0.35,
                max_tokens=6000,
            )
            text = (polished or "").strip()
            if len(text) > 800 and "Executive Summary" in text:
                return text
        except Exception as exc:
            logger.warning("CEO package LLM polish failed: %s", exc)
        return skeleton_md

    def _generate_committee_report_from_dossier(self, dossier: RndDossierOut) -> str:
        """Fallback CR when no committee transcript — from sections."""
        sections = [
            f"### {s.title}\n{(s.content_md or '')[:400]}"
            for s in dossier.sections
            if s.content_md and len(s.content_md) > 30
        ]
        body = "\n\n".join(sections[:8])
        return (
            f"## Décisions actées\n\n"
            f"Synthèse auto depuis sections dossier (pas de transcript comité).\n\n"
            f"## Sections dossier\n\n{body}\n\n"
            f"## Recommandation GO / MAYBE / NO pour le CEO\n\n"
            f"**Verdict :** MAYBE\n\n"
            f"Relire le dossier complet avant décision."
        )

    def _generate_committee_report_llm(
        self,
        dossier: RndDossierOut,
        history: list[dict[str, Any]],
    ) -> str:
        if not self._should_use_llm() or not history:
            return self._generate_committee_report_from_dossier(dossier)

        lines = []
        for msg in history:
            if msg.get("role") == "system":
                continue
            meta = msg.get("metadata") or {}
            if meta.get("synthesis") or meta.get("committee_report"):
                continue
            speaker = msg.get("speaker", "?")
            lines.append(f"{speaker}: {msg.get('content', '')[:1500]}")
        transcript = "\n\n".join(lines)

        user = (
            f"Dossier : {dossier.title} ({dossier.domain})\n\n"
            f"Transcript comité :\n{transcript}\n\n"
            f"{COMMITTEE_REPORT_TEMPLATE}"
        )
        try:
            from agents.rnd_committee_prompts import build_member_system

            return self.llm.complete(
                build_member_system("pm", self._dossier_context(dossier)),
                user,
                agent_id="pm",
                temperature=0.35,
                max_tokens=4000,
            ).strip()
        except Exception as exc:
            logger.warning("committee report LLM failed: %s", exc)
            return self._generate_committee_report_from_dossier(dossier)

    def _dossier_context(self, dossier: RndDossierOut) -> str:
        parts = [f"Titre : {dossier.title}", f"Domaine : {dossier.domain}"]
        for sec in dossier.sections[:6]:
            parts.append(f"\n## {sec.title}\n{(sec.content_md or '')[:800]}")
        return "\n".join(parts)

    def _write_local_package(self, slug: str, markdown: str) -> Path:
        folder = self.data_root / slug
        folder.mkdir(parents=True, exist_ok=True)
        path = folder / "ceo_package.md"
        path.write_text(markdown, encoding="utf-8")
        return path

    def _require_dossier(self, dossier_id: str) -> RndDossierOut:
        dossier = self.repo.get_dossier(dossier_id)
        if not dossier:
            raise ValueError("Dossier introuvable")
        return dossier

    def _load_row_field(self, dossier_id: str, field: str) -> Any:
        try:
            rows = self.repo.db.select("rnd_dossiers", filters={"id": dossier_id}, limit=1)
            if rows:
                return rows[0].get(field)
        except Exception:
            pass
        return None

    def _load_package_json(self, dossier_id: str) -> dict[str, Any] | None:
        val = self._load_row_field(dossier_id, "ceo_package_json")
        return val if isinstance(val, dict) else None

    def _load_committee_report(self, dossier_id: str) -> str | None:
        val = self._load_row_field(dossier_id, "committee_report_md")
        return val if isinstance(val, str) and val.strip() else None

    def _load_dispatch_status(self, dossier_id: str) -> str:
        return self._load_row_field(dossier_id, "dispatch_status") or "pending"

    def _load_dispatch_json(self, dossier_id: str) -> dict[str, Any] | None:
        val = self._load_row_field(dossier_id, "dispatch_json")
        return val if isinstance(val, dict) else None

    def _load_portfolio_rows(self) -> list[dict[str, Any]]:
        try:
            items = self.repo.list_dossiers(limit=30)
            return [i.model_dump() for i in items]
        except Exception:
            return []

    @staticmethod
    def _should_use_llm() -> bool:
        if os.getenv("RND_DOSSIER_USE_LLM", "true").lower() in ("0", "false", "no"):
            return False
        return bool(LLMClient()._settings.openrouter_api_key.strip())
