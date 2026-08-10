"""Dossier CRUD / events mixin."""
from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from services.rnd_repository_dossiers_query import RndDossiersQueryMixin
from services.rnd_repository_helpers import RND_DOSSIERS_ROOT
from services.rnd_schemas import (
    DOMAIN_TO_BRANCH,
    RndDossierOut,
    RndDossierSectionOut,
)

logger = logging.getLogger(__name__)


class RndDossiersMixin(RndDossiersQueryMixin):
    @staticmethod
    def section_keys_for_domain(domain: str | None) -> list[str]:
        domain_norm = (domain or "autre").lower()
        branch = DOMAIN_TO_BRANCH.get(domain_norm, "other")
        if branch == "hub":
            return [
                "problem", "solution", "mvp", "feasibility", "risks", "decision",
            ]
        keys = [
            "problem", "solution", "market", "mvp", "feasibility",
            "business_case", "risks", "decision",
        ]
        if domain_norm in ("hardware", "robotique", "robotics"):
            keys.insert(6, "manufacturing")
        if domain_norm in ("jeu", "game", "gaming"):
            keys.insert(6, "lore")
        keys.extend(["visual_identity", "social_strategy"])
        seen: set[str] = set()
        ordered: list[str] = []
        for k in keys:
            if k not in seen:
                seen.add(k)
                ordered.append(k)
        return ordered

    @staticmethod
    def branch_for_domain(domain: str | None) -> str:
        return DOMAIN_TO_BRANCH.get((domain or "").lower(), "other")

    def _ensure_local_dossier_dir(self, slug: str) -> Path:
        path = RND_DOSSIERS_ROOT / slug
        (path / "sections").mkdir(parents=True, exist_ok=True)
        return path

    def _write_local_dossier_skeleton(self, slug: str, title: str, sections: list[dict]) -> str:
        path = self._ensure_local_dossier_dir(slug)
        md_lines = [f"# {title}", "", f"*Dossier R&D ALNUA ??? {slug}*", "", "---", ""]
        for sec in sections:
            md_lines.append(f"## {sec['title']}")
            md_lines.append("")
            md_lines.append(sec.get("content_md") or "_?? compl??ter._")
            md_lines.append("")
            sec_path = path / "sections" / f"{sec['section_key']}.md"
            sec_path.write_text(
                f"# {sec['title']}\n\n{sec.get('content_md') or '_?? compl??ter._'}\n",
                encoding="utf-8",
            )
        dossier_md = path / "dossier.md"
        dossier_md.write_text("\n".join(md_lines), encoding="utf-8")
        return str(dossier_md.resolve())

    def _section_out(self, row: dict[str, Any]) -> RndDossierSectionOut:
        return RndDossierSectionOut(
            id=str(row["id"]),
            dossier_id=str(row["dossier_id"]),
            section_key=row["section_key"],
            title=row["title"],
            content_md=row.get("content_md", ""),
            status=row.get("status", "draft"),
            sort_order=row.get("sort_order", 0),
            validated_by=row.get("validated_by"),
            validated_at=row.get("validated_at"),
            revision_note=row.get("revision_note"),
        )

    def _dossier_out(
        self,
        row: dict[str, Any],
        sections: list[dict[str, Any]] | None = None,
        idea_legacy_id: str | None = None,
    ) -> RndDossierOut:
        sec_rows = sections or []
        sec_out = [self._section_out(s) for s in sec_rows]
        validated = sum(1 for s in sec_out if s.status == "validated")
        return RndDossierOut(
            id=str(row["id"]),
            idea_id=str(row["idea_id"]),
            idea_legacy_id=idea_legacy_id,
            slug=row["slug"],
            title=row["title"],
            tagline=row.get("tagline"),
            domain=row.get("domain", "autre"),
            branch=row.get("branch"),
            status=row.get("status", "draft"),
            ceo_status=row.get("ceo_status", "pending"),
            ceo_note=row.get("ceo_note"),
            committee_team=row.get("committee_team") or [],
            vision_snapshot=row.get("vision_snapshot"),
            competitive_context=row.get("competitive_context"),
            finance_json=row.get("finance_json"),
            deck_html_path=row.get("deck_html_path"),
            deck_pdf_path=row.get("deck_pdf_path"),
            one_pager_md=row.get("one_pager_md"),
            ceo_package_json=row.get("ceo_package_json"),
            committee_report_md=row.get("committee_report_md"),
            dispatch_json=row.get("dispatch_json"),
            dispatch_status=row.get("dispatch_status", "pending"),
            project_id=str(row["project_id"]) if row.get("project_id") else None,
            local_path=row.get("local_path"),
            sections=sec_out,
            sections_validated_count=validated,
            sections_total_count=len(sec_out),
            created_at=row.get("created_at"),
            updated_at=row.get("updated_at"),
        )

    def log_event(
        self,
        dossier_id: str,
        event_type: str,
        actor: str,
        payload: dict[str, Any] | None = None,
    ) -> None:
        if not self._use_db:
            return
        try:
            self.db.insert(
                "rnd_dossier_events",
                {
                    "dossier_id": dossier_id,
                    "event_type": event_type,
                    "actor": actor,
                    "payload": payload or {},
                },
            )
        except Exception as exc:
            logger.warning("rnd_repository: log_event failed: %s", exc)
