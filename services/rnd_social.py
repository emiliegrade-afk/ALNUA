"""Social calendar repository and phase templates for R&D dossiers (phase 5)."""

from __future__ import annotations

import json
import logging
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from database.supabase_client import SupabaseClient, get_supabase
from services.rnd_schemas import RndSocialCalendarItemOut

logger = logging.getLogger(__name__)

RND_DOSSIERS_ROOT = Path(
    __import__("os").getenv("HUB_REPO_PATH", "C:/Dev/ALUNA_HUB")
) / "data" / "rnd_dossiers"

# Teaser → pre-launch → launch pipeline (spec phase 5)
SOCIAL_PHASE_TEMPLATES: list[dict[str, Any]] = [
    {
        "phase": "internal",
        "milestone": "Cadrage interne — validation du concept",
        "days_offset": 0,
        "content_type": "behind_scenes",
        "platforms": [],
        "notes": "Pas de post public — jalon interne uniquement.",
        "skip_post": True,
    },
    {
        "phase": "behind_scenes",
        "milestone": "Le problème qu'on résout — avant de nommer le produit",
        "days_offset": 5,
        "content_type": "teaser",
        "platforms": ["instagram", "x"],
        "notes": "Angle douleur utilisateur (stats, situation), pas coulisses dev.",
    },
    {
        "phase": "teaser",
        "milestone": "Teaser #1 — problème sans nommer le produit",
        "days_offset": 10,
        "content_type": "teaser",
        "platforms": ["instagram", "tiktok", "x"],
        "notes": "Hook douleur utilisateur, intrigue, CTA soft (sondage / commentaire).",
    },
    {
        "phase": "teaser",
        "milestone": "Teaser #2 — hint solution",
        "days_offset": 14,
        "content_type": "teaser",
        "platforms": ["instagram", "x", "linkedin"],
        "notes": "Révéler partiellement la proposition de valeur.",
    },
    {
        "phase": "pre_launch",
        "milestone": "Pre-launch — waitlist / early access",
        "days_offset": 18,
        "content_type": "announcement",
        "platforms": ["instagram", "linkedin", "x"],
        "notes": "Annoncer l'ouverture prochaine, bénéfice clair, preuve (MVP scope).",
    },
    {
        "phase": "launch",
        "milestone": "Launch day — disponible / beta ouverte",
        "days_offset": 21,
        "content_type": "announcement",
        "platforms": ["instagram", "tiktok", "x", "linkedin", "youtube"],
        "notes": "Annonce complète, lien, pricing si connu, CTA fort.",
    },
    {
        "phase": "post_launch",
        "milestone": "Post-launch — retour utilisateur / tutoriel",
        "days_offset": 28,
        "content_type": "tutorial",
        "platforms": ["youtube", "instagram", "linkedin"],
        "notes": "Quick win utilisateur, social proof ou démo 60s.",
    },
]


class RndSocialRepository:
    def __init__(self, db: SupabaseClient | None = None) -> None:
        self.db = db or get_supabase()

    def list_calendar(self, dossier_id: str) -> list[RndSocialCalendarItemOut]:
        rows = self.db.select(
            "rnd_social_calendar",
            filters={"dossier_id": dossier_id},
            order_by="planned_at",
            ascending=True,
        )
        items: list[RndSocialCalendarItemOut] = []
        for row in rows:
            post = None
            if row.get("post_id"):
                posts = self.db.select(
                    "posts_queue",
                    filters={"id": row["post_id"]},
                    limit=1,
                )
                post = posts[0] if posts else None
            meta = _phase_meta(row.get("phase", ""), row.get("milestone"))
            items.append(
                RndSocialCalendarItemOut(
                    id=str(row["id"]),
                    dossier_id=str(row["dossier_id"]),
                    phase=row["phase"],
                    milestone=row.get("milestone"),
                    planned_at=row.get("planned_at"),
                    post_id=str(row["post_id"]) if row.get("post_id") else None,
                    status=row.get("status", "planned"),
                    notes=row.get("notes"),
                    created_at=row.get("created_at"),
                    post=post,
                    platforms=meta.get("platforms", []),
                    content_type=meta.get("content_type"),
                )
            )
        return items

    def get_calendar_item(self, item_id: str) -> dict[str, Any] | None:
        rows = self.db.select("rnd_social_calendar", filters={"id": item_id}, limit=1)
        return rows[0] if rows else None

    def delete_planned_calendar(self, dossier_id: str) -> int:
        rows = self.db.select(
            "rnd_social_calendar",
            filters={"dossier_id": dossier_id},
        )
        deleted = 0
        for row in rows:
            if row.get("status") in ("planned", "cancelled") and not row.get("post_id"):
                self.db.delete("rnd_social_calendar", row["id"])
                deleted += 1
        return deleted

    def create_calendar_item(
        self,
        dossier_id: str,
        *,
        phase: str,
        milestone: str,
        planned_at: str,
        notes: str | None = None,
    ) -> dict[str, Any]:
        row = self.db.insert(
            "rnd_social_calendar",
            {
                "dossier_id": dossier_id,
                "phase": phase,
                "milestone": milestone,
                "planned_at": planned_at,
                "notes": notes,
                "status": "planned",
            },
        )
        return row[0] if isinstance(row, list) else row

    def update_calendar_item(self, item_id: str, values: dict[str, Any]) -> dict[str, Any]:
        return self.db.update("rnd_social_calendar", item_id, values)

    def list_dossier_posts(self, dossier_id: str) -> list[dict[str, Any]]:
        return self.db.select(
            "posts_queue",
            filters={"rnd_dossier_id": dossier_id},
            order_by="scheduled_at",
            ascending=True,
        )

    def write_local_calendar(self, slug: str, items: list[dict[str, Any]]) -> str:
        folder = RND_DOSSIERS_ROOT / slug / "social"
        folder.mkdir(parents=True, exist_ok=True)
        path = folder / "calendar.json"
        path.write_text(json.dumps(items, ensure_ascii=False, indent=2), encoding="utf-8")
        return str(path.resolve())


SOCIAL_UNLOCK_STATUSES = frozenset({
    "ceo_approved",
    "in_conception",
    "published",
})


class SocialPipelineLockedError(ValueError):
    """Raised when social actions are attempted before CEO approval."""


def is_social_pipeline_unlocked(
    status: str,
    ceo_status: str | None = None,
) -> bool:
    """Posts + calendrier social : après validation CEO, pas pendant R&D."""
    if status in SOCIAL_UNLOCK_STATUSES:
        return True
    return (ceo_status or "") == "approved"


def assert_social_pipeline_unlocked(dossier) -> None:
    """Raise ValueError if dossier still in R&D phase."""
    status = getattr(dossier, "status", None) or dossier.get("status", "draft")
    ceo_status = getattr(dossier, "ceo_status", None) or dossier.get("ceo_status")
    if is_social_pipeline_unlocked(str(status), ceo_status):
        return
    raise SocialPipelineLockedError(
        "Pipeline social verrouillé pendant la phase R&D. "
        "Disponible après validation CEO du dossier "
        f"(statut actuel : {status})."
    )


def get_rnd_social_repository() -> RndSocialRepository:
    return RndSocialRepository()


def _phase_meta(phase: str, milestone: str | None = None) -> dict[str, Any]:
    if milestone:
        for tpl in SOCIAL_PHASE_TEMPLATES:
            if tpl["milestone"] == milestone:
                return tpl
    for tpl in SOCIAL_PHASE_TEMPLATES:
        if tpl["phase"] == phase:
            return tpl
    return {}


def default_launch_anchor() -> datetime:
    return datetime.now(timezone.utc) + timedelta(days=21)


def build_template_calendar(
    dossier_id: str,
    *,
    launch_date: datetime | None = None,
) -> list[dict[str, Any]]:
    """Build calendar rows from templates relative to launch anchor."""
    anchor = launch_date or default_launch_anchor()
    # Align launch phase to anchor; other offsets relative to launch day
    launch_tpl = next(t for t in SOCIAL_PHASE_TEMPLATES if t["phase"] == "launch")
    launch_offset = launch_tpl["days_offset"]

    rows: list[dict[str, Any]] = []
    for tpl in SOCIAL_PHASE_TEMPLATES:
        days = tpl["days_offset"] - launch_offset
        planned = anchor + timedelta(days=days)
        rows.append({
            "dossier_id": dossier_id,
            "phase": tpl["phase"],
            "milestone": tpl["milestone"],
            "planned_at": planned.isoformat(),
            "notes": tpl["notes"],
            "status": "planned",
            "_content_type": tpl["content_type"],
            "_platforms": tpl["platforms"],
        })
    return rows
