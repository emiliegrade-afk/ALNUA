"""R&D CEO agent — dossier I/O helpers and LLM gate."""
from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from agents.base import LLMClient
from services.rnd_schemas import RndDossierOut


class RndCeoHelpersMixin:
    """Requires ``self.repo``, ``self.llm``, ``self.data_root``."""

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

    def _write_local_package(self, slug: str, markdown: str) -> Path:
        folder = self.data_root / slug
        folder.mkdir(parents=True, exist_ok=True)
        path = folder / "ceo_package.md"
        path.write_text(markdown, encoding="utf-8")
        return path

    def _dossier_context(self, dossier: RndDossierOut) -> str:
        parts = [f"Titre : {dossier.title}", f"Domaine : {dossier.domain}"]
        for sec in dossier.sections[:6]:
            parts.append(f"\n## {sec.title}\n{(sec.content_md or '')[:800]}")
        return "\n".join(parts)
