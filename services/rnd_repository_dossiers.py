"""Dossier CRUD / events mixin."""
from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from config.paths import data_dir
from services.rnd_repository_helpers import (
    RND_DOSSIERS_ROOT,
    _is_uuid,
    _slugify,
)
from services.rnd_schemas import (
    DOMAIN_TO_BRANCH,
    RndDossierEventOut,
    RndDossierListItem,
    RndDossierOut,
    RndDossierSectionOut,
)

logger = logging.getLogger(__name__)

class RndDossiersMixin:
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
        # Deduplicate while preserving order
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
    def list_dossiers(
        self,
        status: str | None = None,
        domain: str | None = None,
        limit: int = 50,
    ) -> list[RndDossierListItem]:
        if not self._use_db:
            return []
        try:
            rows = self.db.select("rnd_dossiers", order_by="updated_at", ascending=False, limit=limit)
            if status:
                rows = [r for r in rows if r.get("status") == status]
            if domain:
                rows = [r for r in rows if r.get("domain") == domain]

            items: list[RndDossierListItem] = []
            for row in rows:
                sections = self.db.select(
                    "rnd_dossier_sections",
                    filters={"dossier_id": row["id"]},
                )
                validated = sum(1 for s in sections if s.get("status") == "validated")
                idea_rows = self.db.select("rnd_ideas", filters={"id": row["idea_id"]}, limit=1)
                legacy = idea_rows[0].get("legacy_id") if idea_rows else None
                items.append(
                    RndDossierListItem(
                        id=str(row["id"]),
                        slug=row["slug"],
                        title=row["title"],
                        domain=row.get("domain", "autre"),
                        branch=row.get("branch"),
                        status=row.get("status", "draft"),
                        ceo_status=row.get("ceo_status", "pending"),
                        idea_legacy_id=legacy,
                        sections_validated_count=validated,
                        sections_total_count=len(sections),
                        created_at=row.get("created_at"),
                        updated_at=row.get("updated_at"),
                    )
                )
            return items
        except Exception as exc:
            logger.warning("rnd_repository: list_dossiers failed: %s", exc)
            return []
    def get_dossier(self, dossier_id: str) -> RndDossierOut | None:
        if not self._use_db:
            return None
        try:
            row = self._resolve_dossier_row(dossier_id)
            if not row:
                return None
            sections = self.db.select(
                "rnd_dossier_sections",
                filters={"dossier_id": row["id"]},
                order_by="sort_order",
                ascending=True,
            )
            idea_rows = self.db.select("rnd_ideas", filters={"id": row["idea_id"]}, limit=1)
            legacy = idea_rows[0].get("legacy_id") if idea_rows else None
            dossier = self._dossier_out(row, sections, legacy)
            return self._heal_dossier_status(dossier)
        except Exception as exc:
            logger.warning("rnd_repository: get_dossier failed: %s", exc)
            return None
    def _resolve_dossier_row(self, ref: str) -> dict[str, Any] | None:
        """Resolve dossier by UUID, slug (exact or slugified), or legacy idea id."""
        key = (ref or "").strip()
        if not key:
            return None

        if _is_uuid(key):
            rows = self.db.select("rnd_dossiers", filters={"id": key}, limit=1)
            if rows:
                return rows[0]

        for slug_candidate in (key, _slugify(key)[:60]):
            if not slug_candidate:
                continue
            rows = self.db.select("rnd_dossiers", filters={"slug": slug_candidate}, limit=1)
            if rows:
                return rows[0]

        idea_row = self.get_idea_db_row(key)
        if idea_row and idea_row.get("dossier_id"):
            rows = self.db.select(
                "rnd_dossiers",
                filters={"id": str(idea_row["dossier_id"])},
                limit=1,
            )
            if rows:
                return rows[0]

        return None
    def _heal_dossier_status(self, dossier: RndDossierOut) -> RndDossierOut:
        """Upgrade legacy statuses when a committee CR exists and no session is active."""
        if dossier.status not in ("draft", "committee_active"):
            return dossier
        if not dossier.committee_report_md or len(dossier.committee_report_md.strip()) < 40:
            return dossier
        try:
            from services.rnd_committee import get_committee_repository

            if get_committee_repository().get_active_session(dossier.id):
                return dossier
            healed = self.update_dossier(dossier.id, {"status": "partial_validated"})
            return healed or dossier
        except Exception as exc:
            logger.warning("rnd_repository: heal dossier status failed: %s", exc)
            return dossier
    def get_dossier_events(self, dossier_id: str, limit: int = 50) -> list[RndDossierEventOut]:
        if not self._use_db:
            return []
        try:
            rows = self.db.select(
                "rnd_dossier_events",
                filters={"dossier_id": dossier_id},
                order_by="created_at",
                ascending=False,
                limit=limit,
            )
            return [
                RndDossierEventOut(
                    id=str(r["id"]),
                    dossier_id=str(r["dossier_id"]),
                    event_type=r["event_type"],
                    actor=r["actor"],
                    payload=r.get("payload"),
                    created_at=r.get("created_at", ""),
                )
                for r in rows
            ]
        except Exception as exc:
            logger.warning("rnd_repository: get_dossier_events failed: %s", exc)
            return []
    def update_dossier(self, dossier_id: str, values: dict[str, Any]) -> RndDossierOut | None:
        if not self._use_db:
            return None
        try:
            row = self.db.update("rnd_dossiers", dossier_id, values)
            return self.get_dossier(str(row["id"]))
        except Exception as exc:
            logger.warning("rnd_repository: update_dossier failed: %s", exc)
            return None
    def load_competitive_context(self, limit_chars: int = 3000) -> str:
        """Load latest competitive anti-patterns from data/rnd_competitive/."""
        comp_dir = data_dir("rnd_competitive")
        if not comp_dir.exists():
            return ""
        parts: list[str] = []
        for path in sorted(comp_dir.glob("*.md"), key=lambda p: p.stat().st_mtime, reverse=True)[:3]:
            try:
                parts.append(path.read_text(encoding="utf-8")[:1200])
            except Exception:
                pass
        return "\n\n---\n\n".join(parts)[:limit_chars]
