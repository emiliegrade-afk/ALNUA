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
from agents.rnd_social_agent import ensure_project_for_dossier
from services.rnd_ceo_package import (
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

COMMITTEE_REPORT_TEMPLATE = """Rédige un **compte-rendu de clôture comité R&D** markdown pour Emilie (CEO).
Utilise EXACTEMENT cette structure :

## Décisions actées
[Liste à puces — ce qui a été tranché]

## Sections validées / à revoir
| Section | Statut | Commentaire |
|---------|--------|-------------|

## Actions ouvertes (max 5)
- [ ] ...

## Risques ouverts
- ...

## Recommandation GO / MAYBE / NO pour le CEO
**Verdict :** GO|MAYBE|NO
[2-3 phrases factuelles, sans fluff]

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
            "can_generate": dossier.status in PACKAGE_ELIGIBLE_STATUSES,
            "can_decide": dossier.status == "ready_for_ceo"
            and bool(row_pkg)
            and dossier.ceo_status == "pending",
            "can_dispatch": dossier.ceo_status == "approved"
            and dispatch_status != "dispatched",
        }

    def generate_package(
        self,
        dossier_id: str,
        *,
        actor: str = "rnd_ceo_agent",
        force: bool = False,
    ) -> dict[str, Any]:
        dossier = self._require_dossier(dossier_id)
        if dossier.status not in PACKAGE_ELIGIBLE_STATUSES:
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

        committee_report = self._load_committee_report(dossier_id)
        if not committee_report:
            committee_report = self._generate_committee_report_from_dossier(dossier)

        portfolio_rows = self._load_portfolio_rows()

        markdown = build_ceo_package_md(
            dossier,
            committee_report_md=committee_report,
            portfolio_rows=portfolio_rows,
        )
        package_json = build_ceo_package_json(
            dossier,
            committee_report_md=committee_report,
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

        return {
            "dossier_status": new_status,
            "ceo_status": ceo_status,
            "ceo_note": ceo_note,
            "message": (
                "Projet approuvé — dispatch COO disponible."
                if ceo_status == "approved"
                else "Décision enregistrée."
            ),
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
            return {
                "message": "Dispatch déjà effectué.",
                "dispatch": self._load_dispatch_json(dossier_id),
                "already_dispatched": True,
            }

        package = self._load_package_json(dossier_id) or {}
        matrix = package.get("dispatch_matrix") or build_dispatch_matrix(dossier)
        project_id = ensure_project_for_dossier(dossier, self.repo.db)

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

        # Brief COO via agent_logs for dashboard pickup
        try:
            self.repo.db.insert(
                "agent_logs",
                {
                    "agent_name": "coo_agent",
                    "action": "rnd_dispatch_brief",
                    "project_id": project_id,
                    "input_summary": (
                        f"Nouveau projet validé CEO : {dossier.title}. "
                        f"{len(roadmap_created)} tâches roadmap créées. "
                        f"Consulte /roadmap?project_id={project_id}"
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

        return {
            "message": f"Dispatch COO effectué — {len(roadmap_created)} entrées roadmap.",
            "dispatch": dispatch_payload,
            "roadmap_items": roadmap_created,
            "project_id": project_id,
        }

    def generate_committee_report(
        self,
        dossier_id: str,
        history: list[dict[str, Any]],
        *,
        dossier: RndDossierOut | None = None,
    ) -> str:
        dossier = dossier or self._require_dossier(dossier_id)
        return self._generate_committee_report_llm(dossier, history)

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
            speaker = msg.get("speaker", "?")
            lines.append(f"{speaker}: {msg.get('content', '')[:700]}")
        transcript = "\n\n".join(lines[-40:])

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
                max_tokens=1800,
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
