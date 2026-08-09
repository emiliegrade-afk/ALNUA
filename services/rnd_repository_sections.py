"""Section content / finance / validation mixin."""
from __future__ import annotations

import logging
from typing import Any

from services.rnd_repository_helpers import (
    _now_iso,
)
from services.rnd_schemas import (
    RndDossierOut,
)

logger = logging.getLogger(__name__)

class RndSectionsMixin:
    def update_section_content(
        self,
        dossier_id: str,
        section_key: str,
        content_md: str,
        *,
        status: str | None = None,
        revision_note: str | None = None,
    ) -> None:
        if not self._use_db:
            return
        rows = self.db.select(
            "rnd_dossier_sections",
            filters={"dossier_id": dossier_id, "section_key": section_key},
            limit=1,
        )
        if not rows:
            return
        values: dict[str, Any] = {"content_md": content_md}
        if status:
            values["status"] = status
        if revision_note is not None:
            values["revision_note"] = revision_note
        self.db.update("rnd_dossier_sections", rows[0]["id"], values)
        dossier = self.get_dossier(dossier_id)
        if dossier:
            self._write_local_dossier_skeleton(
                dossier.slug,
                dossier.title,
                [
                    {
                        "section_key": s.section_key,
                        "title": s.title,
                        "content_md": content_md if s.section_key == section_key else s.content_md,
                    }
                    for s in dossier.sections
                ],
            )
    def set_finance_json(self, dossier_id: str, finance: dict[str, Any]) -> None:
        if not self._use_db:
            return
        self.db.update("rnd_dossiers", dossier_id, {"finance_json": finance})
    def validate_section(
        self,
        dossier_id: str,
        section_key: str,
        actor: str,
        note: str | None = None,
    ) -> RndDossierOut | None:
        if not self._use_db:
            return None
        rows = self.db.select(
            "rnd_dossier_sections",
            filters={"dossier_id": dossier_id, "section_key": section_key},
            limit=1,
        )
        if not rows:
            return None
        self.db.update(
            "rnd_dossier_sections",
            rows[0]["id"],
            {
                "status": "validated",
                "validated_by": actor,
                "validated_at": _now_iso(),
                "revision_note": note,
            },
        )
        self.log_event(
            dossier_id,
            "section_validated",
            actor,
            {"section_key": section_key, "note": note},
        )
        return self.get_dossier(dossier_id)
    def request_section_revision(
        self,
        dossier_id: str,
        section_key: str,
        revision_note: str,
        actor: str,
    ) -> RndDossierOut | None:
        if not self._use_db:
            return None
        rows = self.db.select(
            "rnd_dossier_sections",
            filters={"dossier_id": dossier_id, "section_key": section_key},
            limit=1,
        )
        if not rows:
            return None
        self.db.update(
            "rnd_dossier_sections",
            rows[0]["id"],
            {
                "status": "needs_revision",
                "revision_note": revision_note,
                "validated_by": None,
                "validated_at": None,
            },
        )
        self.log_event(
            dossier_id,
            "section_revision_requested",
            actor,
            {"section_key": section_key, "revision_note": revision_note},
        )
        return self.get_dossier(dossier_id)
