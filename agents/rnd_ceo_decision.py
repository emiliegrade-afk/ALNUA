"""R&D CEO agent — Emilie validation and lifecycle updates."""
from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any

from agents.rnd_ceo_errors import CeoDecisionError

logger = logging.getLogger(__name__)


class RndCeoDecisionMixin:
    """Requires dispatch mixin for auto-dispatch after approval."""

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

        dispatch_result: dict[str, Any] | None = None
        dispatch_error: str | None = None
        if ceo_status == "approved" and self._load_dispatch_status(dossier_id) != "dispatched":
            try:
                dispatch_result = self.dispatch_to_coo(dossier_id, actor=actor)
            except Exception as exc:
                dispatch_error = str(exc)
                logger.warning("auto dispatch on CEO approve failed: %s", exc)

        if ceo_status == "approved" and dispatch_result:
            n = len(dispatch_result.get("roadmap_items") or [])
            message = (
                f"Projet approuvé — dispatch COO effectué ({n} tâches, agents notifiés)."
            )
        elif ceo_status == "approved" and self._load_dispatch_status(dossier_id) == "dispatched":
            message = "Projet approuvé — dispatch COO déjà en place."
        elif ceo_status == "approved" and dispatch_error:
            message = (
                "Projet approuvé — dispatch COO à relancer manuellement "
                f"({dispatch_error[:120]})."
            )
        elif ceo_status == "approved":
            message = "Projet approuvé — lance le dispatch COO."
        else:
            message = "Décision enregistrée."

        return {
            "dossier_status": new_status,
            "ceo_status": ceo_status,
            "ceo_note": ceo_note,
            "dispatch": dispatch_result,
            "dispatch_error": dispatch_error,
            "message": message,
        }
