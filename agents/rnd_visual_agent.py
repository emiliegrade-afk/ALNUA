"""Orchestrate visual asset generation for R&D dossiers (phase 4)."""

from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Any

from services.rnd_repository import get_rnd_repository
from services.rnd_schemas import RndDossierAssetOut, RndDossierOut
from services.rnd_visual_generator import ASSET_SPECS, generate_dossier_assets

logger = logging.getLogger(__name__)


class RndVisualAgent:
    AGENT_NAME = "rnd_visual_agent"

    def __init__(self) -> None:
        self.repo = get_rnd_repository()
        self.data_root = Path(
            os.getenv("HUB_REPO_PATH", "C:/Dev/ALUNA_HUB")
        ) / "data" / "rnd_dossiers"

    def list_assets(self, dossier_id: str) -> list[RndDossierAssetOut]:
        dossier = self._require_dossier(dossier_id)
        return self.repo.list_assets(dossier.id)

    def generate_assets(
        self,
        dossier_id: str,
        *,
        force: bool = False,
        actor: str = "rnd_visual_agent",
    ) -> dict[str, Any]:
        dossier = self._require_dossier(dossier_id)
        assets_dir = self.data_root / dossier.slug / "assets"

        if force:
            self.repo.delete_assets(dossier.id)

        rows = generate_dossier_assets(dossier, output_dir=assets_dir, force=force)
        saved: list[dict[str, Any]] = []
        created_count = 0

        for row in rows:
            if row.get("metadata", {}).get("skipped_existing") and not force:
                existing = self.repo.list_assets(dossier.id)
                match = next(
                    (a for a in existing if a.asset_type == row["asset_type"]),
                    None,
                )
                if match:
                    saved.append(match.model_dump())
                    continue
            asset = self.repo.create_asset(row)
            if asset:
                saved.append(asset.model_dump())
                if not row.get("metadata", {}).get("skipped_existing"):
                    created_count += 1

        self.repo.log_event(
            dossier.id,
            "assets_generated",
            actor,
            {"count": created_count, "total": len(saved), "force": force},
        )

        return {
            "dossier_id": dossier.id,
            "assets": saved,
            "created": created_count,
            "expected": len([s for s in ASSET_SPECS if not s.get("requires_finance") or dossier.finance_json]),
            "message": f"{created_count} visuel(s) généré(s) — {len(saved)} au total",
        }

    def _require_dossier(self, dossier_id: str) -> RndDossierOut:
        dossier = self.repo.get_dossier(dossier_id)
        if not dossier:
            raise ValueError("Dossier introuvable")
        return dossier
