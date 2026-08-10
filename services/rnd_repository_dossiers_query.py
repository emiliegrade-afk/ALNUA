"""Dossier CRUD query mixin — list/get/update/events."""

from __future__ import annotations

import logging
from typing import Any

from config.paths import data_dir
from services.rnd_repository_helpers import _is_uuid, _slugify
from services.rnd_schemas import RndDossierEventOut, RndDossierListItem, RndDossierOut

logger = logging.getLogger(__name__)


class RndDossiersQueryMixin:
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
