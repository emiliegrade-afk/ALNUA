"""R&D CEO agent — package generation and committee report LLM passes."""
from __future__ import annotations

import logging
from typing import Any

from config.agent_operating_spec import get_system_prompt
from agents.rnd_ceo_errors import (
    COMMITTEE_REPORT_TEMPLATE,
    CeoPackageNotReadyError,
    ceo_package_eligible,
)
from services.rnd_ceo_package import (
    CEO_PACKAGE_OUTLINE,
    build_ceo_package_json,
    build_ceo_package_md,
)
from services.rnd_schemas import RndDossierOut

logger = logging.getLogger(__name__)


class RndCeoGenerationMixin:
    """Requires helper mixin for dossier loads and local package writes."""

    def generate_package(
        self,
        dossier_id: str,
        *,
        actor: str = "rnd_ceo_agent",
        force: bool = False,
    ) -> dict[str, Any]:
        dossier = self._require_dossier(dossier_id)
        if not ceo_package_eligible(dossier):
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
