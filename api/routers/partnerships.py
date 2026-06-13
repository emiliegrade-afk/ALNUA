"""Auto-split from api/main.py — partnerships routes."""

from __future__ import annotations

from api.route_common import *  # noqa: F403

router = APIRouter()


def _partner_row_to_api(row: dict[str, Any]) -> dict[str, Any]:
    return {
        **row,
        "project_ids": row.get("project_ids") or [],
    }


def _serialize_partner_dates(values: dict[str, Any]) -> dict[str, Any]:
    out = dict(values)
    for key in ("next_followup", "last_contact_date"):
        if key in out and out[key] is not None and hasattr(out[key], "isoformat"):
            out[key] = out[key].isoformat()
    return out


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
    return [_partner_row_to_api(r) for r in rows]


@router.post("/partners")
def create_partner(body: PartnerCreate) -> dict[str, Any]:
    db = get_supabase()
    row = db.insert(
        "partners",
        _serialize_partner_dates(
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
    return _partner_row_to_api(row)


@router.patch("/partners/{partner_id}")
def update_partner(partner_id: str, body: PartnerUpdate) -> dict[str, Any]:
    db = get_supabase()
    rows = db.select("partners", filters={"id": partner_id})
    if not rows:
        raise HTTPException(status_code=404, detail="Partenaire introuvable")
    values = body.model_dump(exclude_none=True)
    if not values:
        raise HTTPException(status_code=400, detail="Aucun champ à mettre à jour")
    updated = db.update("partners", partner_id, _serialize_partner_dates(values))
    return _partner_row_to_api(updated)


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
    return _partner_row_to_api(updated)


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


@router.get("/affiliate-links")
def list_affiliate_links(partner_id: str | None = None) -> list[dict[str, Any]]:
    db = get_supabase()
    filters = {"partner_id": partner_id} if partner_id else None
    return db.select(
        "affiliate_links",
        filters=filters,
        order_by="created_at",
        ascending=False,
    )


@router.post("/affiliate-links")
def create_affiliate_link(body: AffiliateLinkCreate) -> dict[str, Any]:
    db = get_supabase()
    if not db.select("partners", filters={"id": body.partner_id}):
        raise HTTPException(status_code=404, detail="Partenaire introuvable")

    code = (body.code or "").strip().upper() or generate_affiliate_code()
    for _ in range(5):
        existing = db.select("affiliate_links", filters={"code": code})
        if not existing:
            break
        code = generate_affiliate_code()

    row = db.insert(
        "affiliate_links",
        {
            "partner_id": body.partner_id,
            "project_id": body.project_id,
            "code": code,
            "redirect_url": body.redirect_url,
            "commission_type": body.commission_type,
            "commission_value": body.commission_value,
            "active": body.active,
        },
    )
    settings = get_settings()
    base = settings.beta_portal_base_url.replace(":3000", ":8000")
    if "localhost" in base:
        base = f"http://localhost:{settings.api_port}"
    row["public_url"] = affiliate_public_url(code, base)
    return row


@router.patch("/affiliate-links/{link_id}")
def update_affiliate_link(link_id: str, body: AffiliateLinkUpdate) -> dict[str, Any]:
    db = get_supabase()
    rows = db.select("affiliate_links", filters={"id": link_id})
    if not rows:
        raise HTTPException(status_code=404, detail="Lien affilié introuvable")
    values = body.model_dump(exclude_none=True)
    if not values:
        raise HTTPException(status_code=400, detail="Aucun champ à mettre à jour")
    return db.update("affiliate_links", link_id, values)


@router.get("/affiliate-links/{link_id}/timeline")
def affiliate_link_timeline_endpoint(
    link_id: str,
    days: int = Query(default=30, ge=1, le=90),
) -> list[dict[str, Any]]:
    db = get_supabase()
    if not db.select("affiliate_links", filters={"id": link_id}):
        raise HTTPException(status_code=404, detail="Lien affilié introuvable")
    return affiliate_link_timeline(db, link_id, days)


@router.get("/go/{code}")
def affiliate_redirect(
    code: str,
    user_agent: str | None = Header(default=None, alias="User-Agent"),
    referer: str | None = Header(default=None, alias="Referer"),
):
    db = get_supabase()
    rows = db.select("affiliate_links", filters={"code": code.upper()})
    if not rows or not rows[0].get("active"):
        return RedirectResponse(url=AFFILIATE_FALLBACK_URL, status_code=302)
    link = rows[0]
    try:
        record_affiliate_click(db, link, user_agent, referer)
    except Exception:
        logger.exception("Affiliate click logging failed for code=%s", code)
    return RedirectResponse(url=link["redirect_url"], status_code=302)


@router.post("/go/{code}/conversion")
def affiliate_conversion(code: str, body: AffiliateConversionBody) -> dict[str, Any]:
    db = get_supabase()
    rows = db.select("affiliate_links", filters={"code": code.upper()})
    if not rows:
        raise HTTPException(status_code=404, detail="Lien affilié introuvable")
    return record_affiliate_conversion(db, rows[0], body.revenue)


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
        "partner": _partner_row_to_api(partner),
        "request_id": request_id,
    }


