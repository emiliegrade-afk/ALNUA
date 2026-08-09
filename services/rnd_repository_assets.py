"""Dossier assets / deck paths mixin."""
from __future__ import annotations

import logging
from typing import Any

from services.rnd_schemas import (
    RndDossierAssetOut,
    RndDossierOut,
)

logger = logging.getLogger(__name__)

class RndAssetsMixin:
    def list_assets(self, dossier_id: str) -> list[RndDossierAssetOut]:
        if not self._use_db:
            return []
        try:
            rows = self.db.select(
                "rnd_dossier_assets",
                filters={"dossier_id": dossier_id},
                order_by="created_at",
                ascending=False,
            )
            return [
                RndDossierAssetOut(
                    id=str(r["id"]),
                    dossier_id=str(r["dossier_id"]),
                    section_key=r.get("section_key"),
                    asset_type=r["asset_type"],
                    file_path=r["file_path"],
                    public_url=r.get("public_url"),
                    image_prompt=r.get("image_prompt"),
                    generation_model=r.get("generation_model"),
                    width=r.get("width"),
                    height=r.get("height"),
                    metadata=r.get("metadata"),
                    created_at=r.get("created_at"),
                )
                for r in rows
            ]
        except Exception as exc:
            logger.warning("rnd_repository: list_assets failed: %s", exc)
            return []
    def create_asset(self, values: dict[str, Any]) -> RndDossierAssetOut | None:
        if not self._use_db:
            return None
        try:
            row = self.db.insert("rnd_dossier_assets", values)
            row = row[0] if isinstance(row, list) else row
            return RndDossierAssetOut(
                id=str(row["id"]),
                dossier_id=str(row["dossier_id"]),
                section_key=row.get("section_key"),
                asset_type=row["asset_type"],
                file_path=row["file_path"],
                public_url=row.get("public_url"),
                image_prompt=row.get("image_prompt"),
                generation_model=row.get("generation_model"),
                width=row.get("width"),
                height=row.get("height"),
                metadata=row.get("metadata"),
                created_at=row.get("created_at"),
            )
        except Exception as exc:
            logger.warning("rnd_repository: create_asset failed: %s", exc)
            return None
    def delete_assets(self, dossier_id: str) -> None:
        if not self._use_db:
            return
        try:
            rows = self.db.select("rnd_dossier_assets", filters={"dossier_id": dossier_id})
            for row in rows:
                self.db.delete("rnd_dossier_assets", row["id"])
        except Exception as exc:
            logger.warning("rnd_repository: delete_assets failed: %s", exc)
    def set_deck_paths(
        self,
        dossier_id: str,
        *,
        html_path: str | None,
        pdf_path: str | None = None,
        one_pager_md: str | None = None,
    ) -> RndDossierOut | None:
        if not self._use_db:
            return None
        values: dict[str, Any] = {}
        if html_path is not None:
            values["deck_html_path"] = html_path
        if pdf_path is not None:
            values["deck_pdf_path"] = pdf_path
        if one_pager_md is not None:
            values["one_pager_md"] = one_pager_md
        if not values:
            return self.get_dossier(dossier_id)
        try:
            self.db.update("rnd_dossiers", dossier_id, values)
            return self.get_dossier(dossier_id)
        except Exception as exc:
            logger.warning("rnd_repository: set_deck_paths failed: %s", exc)
            return None
