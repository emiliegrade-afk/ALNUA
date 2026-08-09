"""Campaigns CRUD — Phase 33, ROADMAP.md (Marketing Command Center)."""

from __future__ import annotations

from api.route_common import *  # noqa: F403

router = APIRouter()


def _campaign_row(body: CampaignCreate) -> dict[str, Any]:
    return {
        "name": body.name,
        "objective": body.objective,
        "platform": body.platform,
        "status": body.status,
        "budget_allocated_usd": body.budget_allocated_usd,
        "project_id": body.project_id,
        "audience": body.audience,
        "brief": body.brief,
        "start_date": body.start_date.isoformat() if body.start_date else None,
        "end_date": body.end_date.isoformat() if body.end_date else None,
    }


def _attach_spent(db: Any, rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Somme les vraies transactions.amount liées à chaque campagne (spent_usd),
    puis dérive roi_pct UNIQUEMENT si un revenue_generated_usd a été saisi
    manuellement (Phase 37) — jamais de ROI affiché tant que ce champ est
    None, jamais de division par un spent_usd à 0."""
    if not rows:
        return rows
    all_transactions = db.select("transactions", filters={"type": "expense"})
    spent_by_campaign: dict[str, float] = {}
    for tx in all_transactions:
        campaign_id = tx.get("campaign_id")
        if not campaign_id:
            continue
        spent_by_campaign[campaign_id] = spent_by_campaign.get(campaign_id, 0.0) + float(
            tx.get("amount") or 0
        )
    for row in rows:
        spent = round(spent_by_campaign.get(row["id"], 0.0), 2)
        row["spent_usd"] = spent
        revenue = row.get("revenue_generated_usd")
        row["roi_pct"] = round((revenue - spent) / spent * 100, 1) if revenue is not None and spent > 0 else None
    return rows


@router.get("/campaigns")
def list_campaigns(
    project_id: str | None = None,
    status: str | None = None,
    platform: str | None = None,
) -> list[dict[str, Any]]:
    db = get_supabase()
    filters: dict[str, Any] = {}
    if project_id:
        filters["project_id"] = project_id
    if status:
        filters["status"] = status
    if platform:
        filters["platform"] = platform
    rows = db.select("campaigns", filters=filters or None, order_by="created_at", ascending=False)
    return _attach_spent(db, rows)


@router.post("/campaigns")
def create_campaign(body: CampaignCreate) -> dict[str, Any]:
    db = get_supabase()
    row = db.insert("campaigns", _campaign_row(body))
    return _attach_spent(db, [row])[0]


_STATS_FIELDS = {"reach", "engagements", "conversions", "revenue_generated_usd"}


@router.patch("/campaigns/{campaign_id}")
def update_campaign(campaign_id: str, body: CampaignUpdate) -> dict[str, Any]:
    db = get_supabase()
    rows = db.select("campaigns", filters={"id": campaign_id})
    if not rows:
        raise HTTPException(status_code=404, detail="Campagne introuvable")

    updates = body.model_dump(exclude_unset=True)
    if "start_date" in updates and updates["start_date"] is not None:
        updates["start_date"] = updates["start_date"].isoformat()
    if "end_date" in updates and updates["end_date"] is not None:
        updates["end_date"] = updates["end_date"].isoformat()
    if _STATS_FIELDS & updates.keys():
        updates["stats_updated_at"] = datetime.now(timezone.utc).isoformat()
    if not updates:
        return _attach_spent(db, rows)[0]
    row = db.update("campaigns", campaign_id, updates)
    return _attach_spent(db, [row])[0]


@router.get("/campaigns/performance-by-platform")
def performance_by_platform() -> list[dict[str, Any]]:
    """Agrège reach/engagements/conversions/spent/revenue par plateforme ad
    (meta/google/tiktok), uniquement sur les campagnes où au moins une stat
    a été saisie manuellement. sample_size expose combien de campagnes sont
    comptées — jamais présenté comme une couverture complète du canal."""
    db = get_supabase()
    rows = _attach_spent(db, db.select("campaigns"))
    by_platform: dict[str, dict[str, Any]] = {}
    for row in rows:
        if row.get("stats_updated_at") is None:
            continue
        platform = row["platform"]
        bucket = by_platform.setdefault(
            platform,
            {"platform": platform, "sample_size": 0, "reach": 0, "engagements": 0,
             "conversions": 0, "spent_usd": 0.0, "revenue_generated_usd": 0.0,
             "has_revenue": False},
        )
        bucket["sample_size"] += 1
        bucket["reach"] += row.get("reach") or 0
        bucket["engagements"] += row.get("engagements") or 0
        bucket["conversions"] += row.get("conversions") or 0
        bucket["spent_usd"] += row.get("spent_usd") or 0.0
        if row.get("revenue_generated_usd") is not None:
            bucket["revenue_generated_usd"] += row["revenue_generated_usd"]
            bucket["has_revenue"] = True
    result = []
    for bucket in by_platform.values():
        spent = round(bucket["spent_usd"], 2)
        revenue = round(bucket["revenue_generated_usd"], 2) if bucket["has_revenue"] else None
        result.append({
            "platform": bucket["platform"],
            "sample_size": bucket["sample_size"],
            "reach": bucket["reach"],
            "engagements": bucket["engagements"],
            "conversions": bucket["conversions"],
            "spent_usd": spent,
            "revenue_generated_usd": revenue,
            "roi_pct": round((revenue - spent) / spent * 100, 1) if revenue is not None and spent > 0 else None,
        })
    result.sort(key=lambda r: r["reach"], reverse=True)
    return result


@router.delete("/campaigns/{campaign_id}")
def delete_campaign(campaign_id: str) -> dict[str, bool]:
    db = get_supabase()
    rows = db.select("campaigns", filters={"id": campaign_id})
    if not rows:
        raise HTTPException(status_code=404, detail="Campagne introuvable")
    db.delete("campaigns", campaign_id)
    return {"ok": True}
