"""R&D CEO agent — package read API and CEO bureau queue."""
from __future__ import annotations

import logging
from typing import Any

from agents.rnd_ceo_errors import ceo_package_eligible

logger = logging.getLogger(__name__)


class RndCeoQueueMixin:
    """Requires helper mixin methods for dossier/package loads."""

    def get_package(self, dossier_id: str) -> dict[str, Any]:
        dossier = self._require_dossier(dossier_id)
        row_pkg = dossier.ceo_package_json or self._load_package_json(dossier_id)
        committee_report = dossier.committee_report_md or self._load_committee_report(dossier_id)
        dispatch_status = dossier.dispatch_status or self._load_dispatch_status(dossier_id)
        dispatch_json = dossier.dispatch_json or self._load_dispatch_json(dossier_id)
        return {
            "dossier_id": dossier.id,
            "dossier_status": dossier.status,
            "ceo_status": dossier.ceo_status,
            "ceo_note": dossier.ceo_note,
            "dispatch_status": dispatch_status,
            "committee_report_md": committee_report,
            "package": row_pkg,
            "dispatch": dispatch_json,
            "markdown": (row_pkg or {}).get("markdown") or dossier.one_pager_md,
            "can_generate": ceo_package_eligible(dossier),
            "can_decide": dossier.status == "ready_for_ceo"
            and bool(row_pkg)
            and dossier.ceo_status == "pending",
            "can_dispatch": dossier.ceo_status == "approved"
            and dispatch_status != "dispatched",
        }

    def list_pending_dossiers(self, *, limit: int = 20) -> list[dict[str, Any]]:
        """Dossiers with CEO package generated, awaiting Emilie's decision."""
        queue = self.list_ceo_queue(limit=limit)
        return queue["to_validate"]

    def list_ceo_queue(self, *, limit: int = 20) -> dict[str, list[dict[str, Any]]]:
        """CEO bureau queue: ready to decide vs needs package generation."""
        if not self.repo._use_db:
            return {"to_validate": [], "to_prepare": []}
        try:
            rows = self.repo.db.select(
                "rnd_dossiers",
                order_by="updated_at",
                ascending=False,
                limit=max(limit * 4, 40),
            )
        except Exception as exc:
            logger.warning("list_ceo_queue failed: %s", exc)
            return {"to_validate": [], "to_prepare": []}

        to_validate: list[dict[str, Any]] = []
        to_prepare: list[dict[str, Any]] = []

        for row in rows:
            if row.get("ceo_status") != "pending":
                continue
            if row.get("status") in ("ceo_approved", "ceo_rejected", "archived"):
                continue

            pkg = row.get("ceo_package_json")
            has_cr = bool((row.get("committee_report_md") or "").strip())
            status = row.get("status", "draft")
            item = self._ceo_queue_item(row, pkg)

            if pkg and status in ("ready_for_ceo", "partial_validated"):
                to_validate.append(item)
            elif not pkg and (
                status in ("partial_validated", "ready_for_ceo")
                or (status == "draft" and has_cr)
                or (status == "committee_active" and has_cr)
            ):
                item["needs_action"] = "generate_package"
                to_prepare.append(item)

            if len(to_validate) >= limit and len(to_prepare) >= limit:
                break

        return {
            "to_validate": to_validate[:limit],
            "to_prepare": to_prepare[:limit],
        }

    @staticmethod
    def _ceo_queue_item(row: dict[str, Any], pkg: Any) -> dict[str, Any]:
        recommendation = None
        branch = None
        if isinstance(pkg, dict):
            recommendation = pkg.get("recommendation")
            branch = pkg.get("branch")
        return {
            "id": str(row["id"]),
            "slug": row.get("slug"),
            "title": row.get("title"),
            "domain": row.get("domain", "autre"),
            "branch": branch or row.get("branch"),
            "status": row.get("status"),
            "ceo_status": row.get("ceo_status", "pending"),
            "recommendation": recommendation,
            "updated_at": row.get("updated_at"),
            "can_decide": bool(pkg) and row.get("status") == "ready_for_ceo",
            "has_committee_report": bool((row.get("committee_report_md") or "").strip()),
        }
