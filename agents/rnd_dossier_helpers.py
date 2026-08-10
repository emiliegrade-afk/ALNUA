"""R&D dossier agent — shared helpers and status sync."""
from __future__ import annotations

import os

from agents.rnd_dossier_constants import FLUFF_PATTERNS


class RndDossierHelpersMixin:
    """Requires ``self.repo`` from ``RndDossierAgent.__init__``."""

    def _should_use_llm(self) -> bool:
        if os.getenv("RND_DOSSIER_USE_LLM", "true").lower() in ("0", "false", "no"):
            return False
        return bool(self.llm._settings.openrouter_api_key.strip())

    @staticmethod
    def _contains_fluff(text: str) -> bool:
        return bool(FLUFF_PATTERNS.search(text))

    @staticmethod
    def _is_section_placeholder(content_md: str) -> bool:
        """True when section has no user/agent content worth preserving."""
        t = (content_md or "").strip()
        if not t or len(t) < 25:
            return True
        placeholders = (
            "_À compléter",
            "_Business case à générer",
            "_Risques à identifier",
        )
        return any(t.startswith(p) for p in placeholders)

    def _sync_dossier_status(self, dossier_id: str) -> None:
        dossier = self.repo.get_dossier(dossier_id)
        if not dossier:
            return
        validated = dossier.sections_validated_count
        total = dossier.sections_total_count
        if validated == 0:
            status = "draft"
        elif validated < total:
            status = "partial_validated"
        else:
            status = "ready_for_ceo"
        self.repo.update_dossier(dossier_id, {"status": status})
