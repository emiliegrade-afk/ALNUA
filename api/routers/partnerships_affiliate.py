"""Affiliate links and redirect routes."""

from __future__ import annotations

from api.route_common import *  # noqa: F403

router = APIRouter()


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
