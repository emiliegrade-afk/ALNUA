"""Partners CRUD, interactions, and contract routes."""

from __future__ import annotations

from datetime import date

from api.route_common import *  # noqa: F403
from api.routers.partnerships_helpers import partner_row_to_api, serialize_partner_dates

router = APIRouter()


@router.get("/partners")
def list_partners(
    type: str | None = None,
    status: str | None = None,
    direction: str | None = None,
    project_id: str | None = None,
) -> list[dict[str, Any]]:
    db = get_supabase()
    filters: dict[str, Any] = {}
    if type:
        filters["type"] = type
    if status:
        filters["status"] = status
    if direction:
        filters["direction"] = direction
    rows = db.select(
        "partners",
        filters=filters or None,
        order_by="updated_at",
        ascending=False,
    )
    if project_id:
        rows = [r for r in rows if project_id in (r.get("project_ids") or [])]
    return [partner_row_to_api(r) for r in rows]


@router.post("/partners")
def create_partner(body: PartnerCreate) -> dict[str, Any]:
    db = get_supabase()
    row = db.insert(
        "partners",
        serialize_partner_dates(
            {
                "type": body.type,
                "direction": body.direction,
                "name": body.name,
                "status": body.status,
                "company": body.company,
                "email": body.email,
                "instagram_url": body.instagram_url,
                "tiktok_url": body.tiktok_url,
                "youtube_url": body.youtube_url,
                "website": body.website,
                "audience_size": body.audience_size,
                "audience_description": body.audience_description,
                "project_ids": body.project_ids or [],
                "notes": body.notes or "",
                "next_followup": body.next_followup,
                "last_contact_date": body.last_contact_date,
            }
        ),
    )
    return partner_row_to_api(row)


@router.patch("/partners/{partner_id}")
def update_partner(partner_id: str, body: PartnerUpdate) -> dict[str, Any]:
    db = get_supabase()
    rows = db.select("partners", filters={"id": partner_id})
    if not rows:
        raise HTTPException(status_code=404, detail="Partenaire introuvable")
    values = body.model_dump(exclude_none=True)
    if not values:
        raise HTTPException(status_code=400, detail="Aucun champ à mettre à jour")
    updated = db.update("partners", partner_id, serialize_partner_dates(values))
    return partner_row_to_api(updated)


@router.get("/partners/stats")
def partners_stats() -> dict[str, Any]:
    return partnership_stats(get_supabase())


@router.delete("/partners/{partner_id}")
def delete_partner(partner_id: str) -> dict[str, str]:
    db = get_supabase()
    rows = db.select("partners", filters={"id": partner_id})
    if not rows:
        raise HTTPException(status_code=404, detail="Partenaire introuvable")
    db.delete("partners", partner_id)
    return {"status": "deleted", "id": partner_id}


@router.get("/partners/{partner_id}/interactions")
def list_partner_interactions(partner_id: str) -> list[dict[str, Any]]:
    db = get_supabase()
    if not db.select("partners", filters={"id": partner_id}):
        raise HTTPException(status_code=404, detail="Partenaire introuvable")
    return db.select(
        "partner_interactions",
        filters={"partner_id": partner_id},
        order_by="date",
        ascending=False,
    )


@router.post("/partners/{partner_id}/interactions")
def create_partner_interaction(
    partner_id: str,
    body: PartnerInteractionCreate,
) -> dict[str, Any]:
    db = get_supabase()
    partner_rows = db.select("partners", filters={"id": partner_id})
    if not partner_rows:
        raise HTTPException(status_code=404, detail="Partenaire introuvable")
    payload: dict[str, Any] = {
        "partner_id": partner_id,
        "type": body.type,
        "note": body.note or "",
    }
    if body.date:
        payload["date"] = body.date.isoformat()
    row = db.insert("partner_interactions", payload)
    db.update(
        "partners",
        partner_id,
        {"last_contact_date": date.today().isoformat()},
    )
    return row


@router.get("/partners/{partner_id}/contract")
def get_partner_contract(partner_id: str) -> dict[str, str | None]:
    db = get_supabase()
    rows = db.select("partners", filters={"id": partner_id})
    if not rows:
        raise HTTPException(status_code=404, detail="Partenaire introuvable")
    return {"contract_path": rows[0].get("contract_path")}


@router.post("/partners/{partner_id}/contract")
async def upload_partner_contract(
    partner_id: str,
    file: UploadFile = File(...),
) -> dict[str, Any]:
    db = get_supabase()
    rows = db.select("partners", filters={"id": partner_id})
    if not rows:
        raise HTTPException(status_code=404, detail="Partenaire introuvable")
    partner = rows[0]
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Fichier PDF requis")

    dest = build_contract_path(partner["name"], partner["type"])
    dest.parent.mkdir(parents=True, exist_ok=True)
    content = await file.read()
    dest.write_bytes(content)

    updated = db.update(
        "partners",
        partner_id,
        {"contract_path": str(dest)},
    )
    return partner_row_to_api(updated)


@router.get("/partners/{partner_id}/contract/open")
def open_partner_contract(partner_id: str) -> dict[str, bool]:
    db = get_supabase()
    rows = db.select("partners", filters={"id": partner_id})
    if not rows:
        raise HTTPException(status_code=404, detail="Partenaire introuvable")
    path = rows[0].get("contract_path")
    if not path:
        raise HTTPException(status_code=404, detail="Aucun contrat enregistré")
    try:
        open_contract_file(path)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except OSError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    return {"ok": True}


@router.post("/partners/contracts/open-folder")
def open_contracts_folder_endpoint() -> dict[str, bool]:
    try:
        open_contracts_folder()
    except OSError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    return {"ok": True, "path": str(CONTRACTS_ROOT)}
