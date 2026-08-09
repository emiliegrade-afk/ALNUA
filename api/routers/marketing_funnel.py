"""Entonnoir de conversion Marketing — Phase 37, ROADMAP.md.

Saisie mensuelle manuelle par produit (Visiteurs → Intéressés → Engagés →
Abonnés → Clients), jamais une extrapolation. La source réelle vit dans les
outils analytics propres à chaque produit (App Store Connect, Play Console,
Plausible/GA4, signups Supabase) — pas de tracking centralisé côté Hub
aujourd'hui, donc pas de calcul automatique possible tant que ça n'existe
pas. `source_note` documente d'où vient le chiffre saisi.
"""

from __future__ import annotations

from api.route_common import *  # noqa: F403

router = APIRouter()


@router.get("/marketing/funnel")
def list_funnel_snapshots(project_id: str | None = None, limit: int = 12) -> list[dict[str, Any]]:
    db = get_supabase()
    filters = {"project_id": project_id} if project_id else None
    return db.select(
        "funnel_snapshots", filters=filters, order_by="period_month", ascending=False, limit=limit
    )


@router.get("/marketing/funnel/latest")
def latest_funnel_snapshot(project_id: str) -> dict[str, Any] | None:
    db = get_supabase()
    rows = db.select(
        "funnel_snapshots",
        filters={"project_id": project_id},
        order_by="period_month",
        ascending=False,
        limit=1,
    )
    return rows[0] if rows else None


@router.post("/marketing/funnel")
def upsert_funnel_snapshot(body: FunnelSnapshotUpsert) -> dict[str, Any]:
    db = get_supabase()
    period_first_of_month = body.period_month.replace(day=1).isoformat()
    existing = db.select(
        "funnel_snapshots",
        filters={"project_id": body.project_id, "period_month": period_first_of_month},
    )
    payload = {
        "project_id": body.project_id,
        "period_month": period_first_of_month,
        "visitors": body.visitors,
        "interested": body.interested,
        "engaged": body.engaged,
        "subscribers": body.subscribers,
        "customers": body.customers,
        "source_note": body.source_note,
        "entered_by_agent_id": body.entered_by_agent_id,
    }
    if existing:
        return db.update("funnel_snapshots", existing[0]["id"], payload)
    return db.insert("funnel_snapshots", payload)
