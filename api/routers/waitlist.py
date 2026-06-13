"""Auto-split from api/main.py — waitlist routes."""

from __future__ import annotations

from api.route_common import *  # noqa: F403

router = APIRouter()


@router.get("/waitlist/info/{project_slug}")
def waitlist_info(project_slug: str) -> dict[str, Any]:
    db = get_supabase()
    project = resolve_project_by_slug(db, project_slug)
    return {
        "project_id": project["id"],
        "project_name": project["name"],
        "project_slug": project_slug_for(project),
        "description": project.get("description") or "",
        "status": project.get("status"),
    }


@router.get("/waitlist/count/{project_slug}")
def waitlist_count(project_slug: str) -> dict[str, int]:
    db = get_supabase()
    project = resolve_project_by_slug(db, project_slug)
    rows = db.select("waitlist", filters={"project_id": project["id"]})
    return {"count": len(rows)}


@router.post("/waitlist/join")
def waitlist_join(body: WaitlistJoinRequest) -> dict[str, int]:
    db = get_supabase()
    project = resolve_project_by_slug(db, body.project_slug)
    email = body.email.strip().lower()

    existing = db.select(
        "waitlist",
        filters={"project_id": project["id"], "email": email},
    )
    if existing:
        entry = existing[0]
    else:
        entry = db.insert(
            "waitlist",
            {
                "project_id": project["id"],
                "email": email,
                "first_name": (body.first_name or "").strip() or None,
                "source": (body.source or "direct").strip() or "direct",
                "message": (body.message or "").strip() or None,
                "status": "waiting",
            },
        )

    position, total = compute_position(db, project["id"], entry["id"])
    return {"position": position, "total": total}


@router.get("/waitlist")
def waitlist_list(
    project_id: str | None = None,
    status: str | None = None,
    source: str | None = None,
) -> list[dict[str, Any]]:
    db = get_supabase()
    filters: dict[str, Any] = {}
    if project_id:
        filters["project_id"] = project_id
    if status:
        filters["status"] = status
    if source:
        filters["source"] = source

    rows = db.select(
        "waitlist",
        filters=filters or None,
        order_by="created_at",
        ascending=False,
    )
    projects = {p["id"]: p["name"] for p in db.select("projects")}
    for row in rows:
        row["project_name"] = projects.get(row.get("project_id"), "")
    return rows


@router.get("/waitlist/stats")
def waitlist_stats_endpoint(project_id: str | None = None) -> dict[str, Any]:
    db = get_supabase()
    return waitlist_stats(db, project_id=project_id)


@router.post("/waitlist/notify")
def waitlist_notify(body: WaitlistNotifyRequest) -> dict[str, Any]:
    db = get_supabase()
    filters: dict[str, Any] = {"project_id": body.project_id}
    if body.status_filter:
        filters["status"] = body.status_filter
    else:
        filters["status"] = "waiting"

    rows = db.select("waitlist", filters=filters)
    now = datetime.now(timezone.utc).isoformat()
    notified_count = 0

    for row in rows:
        db.update(
            "waitlist",
            row["id"],
            {"status": "notified", "notified_at": now},
        )
        notified_count += 1

    preview_html = markdown_to_html(body.message_md, subject=body.subject)
    return {"notified_count": notified_count, "preview_html": preview_html}


@router.post("/waitlist/generate-email")
def waitlist_generate_email(body: WaitlistGenerateEmailRequest) -> dict[str, str]:
    db = get_supabase()
    try:
        return generate_waitlist_email(db, body.project_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except Exception as exc:
        logger.exception("waitlist_generate_email failed")
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.patch("/waitlist/{entry_id}")
def waitlist_update_status(entry_id: str, body: WaitlistStatusUpdate) -> dict[str, Any]:
    db = get_supabase()
    rows = db.select("waitlist", filters={"id": entry_id})
    if not rows:
        raise HTTPException(status_code=404, detail="Inscription introuvable")
    values: dict[str, Any] = {"status": body.status}
    if body.status == "notified":
        values["notified_at"] = datetime.now(timezone.utc).isoformat()
    return db.update("waitlist", entry_id, values)


@router.delete("/waitlist/{entry_id}")
def waitlist_delete(entry_id: str) -> dict[str, bool]:
    db = get_supabase()
    rows = db.select("waitlist", filters={"id": entry_id})
    if not rows:
        raise HTTPException(status_code=404, detail="Inscription introuvable")
    db.delete("waitlist", entry_id)
    return {"ok": True}


@router.get("/waitlist/export/{project_id}")
def waitlist_export(project_id: str) -> StreamingResponse:
    db = get_supabase()
    rows = db.select(
        "waitlist",
        filters={"project_id": project_id},
        order_by="created_at",
        ascending=True,
    )
    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(["email", "prénom", "source", "date"])
    for row in rows:
        writer.writerow([
            row.get("email") or "",
            row.get("first_name") or "",
            row.get("source") or "",
            row.get("created_at") or "",
        ])
    buffer.seek(0)
    return StreamingResponse(
        iter([buffer.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": 'attachment; filename="waitlist.csv"'},
    )


@router.get("/waitlist/page-url/{project_id}")
def waitlist_page_url(project_id: str) -> dict[str, str]:
    db = get_supabase()
    rows = db.select("projects", filters={"id": project_id})
    if not rows:
        raise HTTPException(status_code=404, detail="Projet introuvable")
    slug = project_slug_for(rows[0])
    return {"page_url": waitlist_url_for_slug(slug), "project_slug": slug}


