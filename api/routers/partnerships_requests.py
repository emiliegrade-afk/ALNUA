"""Partnership inbound request routes."""

from __future__ import annotations

from api.route_common import *  # noqa: F403
from api.routers.partnerships_helpers import partner_row_to_api

router = APIRouter()


@router.post("/partnerships/request")
def create_partnership_request(body: PartnershipRequestCreate) -> dict[str, Any]:
    db = get_supabase()
    return db.insert(
        "partnership_requests",
        body.model_dump(),
    )


@router.get("/partnerships/requests")
def list_partnership_requests(
    status: str | None = None,
) -> list[dict[str, Any]]:
    db = get_supabase()
    filters = {"status": status} if status else None
    return db.select(
        "partnership_requests",
        filters=filters,
        order_by="created_at",
        ascending=False,
    )


@router.patch("/partnerships/requests/{request_id}")
def update_partnership_request(
    request_id: str,
    body: PartnershipRequestUpdate,
) -> dict[str, Any]:
    db = get_supabase()
    rows = db.select("partnership_requests", filters={"id": request_id})
    if not rows:
        raise HTTPException(status_code=404, detail="Demande introuvable")
    values = body.model_dump(exclude_none=True)
    if not values:
        raise HTTPException(status_code=400, detail="Aucun champ à mettre à jour")
    return db.update("partnership_requests", request_id, values)


@router.post("/partnerships/requests/{request_id}/convert")
def convert_partnership_request(request_id: str) -> dict[str, Any]:
    db = get_supabase()
    req_rows = db.select("partnership_requests", filters={"id": request_id})
    if not req_rows:
        raise HTTPException(status_code=404, detail="Demande introuvable")
    req = req_rows[0]

    partner_type = req.get("type") or "other"
    if partner_type == "other":
        partner_type = "creator"

    audience = parse_audience_size_text(req.get("audience_size"))

    partner = db.insert(
        "partners",
        {
            "type": partner_type,
            "direction": "inbound",
            "name": req["name"],
            "email": req.get("email"),
            "instagram_url": req.get("instagram_url"),
            "tiktok_url": req.get("tiktok_url"),
            "website": req.get("website"),
            "audience_size": audience,
            "audience_description": req.get("audience_size"),
            "notes": req.get("message") or "",
            "status": "prospect",
        },
    )

    db.update(
        "partnership_requests",
        request_id,
        {"status": "converted", "partner_id": partner["id"]},
    )
    return {
        "partner": partner_row_to_api(partner),
        "request_id": request_id,
    }
