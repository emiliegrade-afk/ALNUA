"""Auto-split from api/main.py — beta routes."""

from __future__ import annotations

from api.route_common import *  # noqa: F403

router = APIRouter()


@router.get("/beta/info/{project_slug}")
def beta_info(project_slug: str) -> dict[str, Any]:
    db = get_supabase()
    project = resolve_project_by_slug(db, project_slug)
    version = latest_app_version(db, project["id"])
    return {
        "project_id": project["id"],
        "project_name": project["name"],
        "project_slug": project_slug_for(project),
        "app_version": version,
        "test_instructions": project.get("description") or "",
        "status": project.get("status"),
    }


@router.post("/beta/register")
def beta_register(body: BetaRegisterRequest) -> dict[str, Any]:
    db = get_supabase()
    project = resolve_project_by_slug(db, body.project_slug)
    email = body.email.strip().lower()

    existing = db.select(
        "beta_testers",
        filters={"project_id": project["id"], "email": email},
    )
    if existing:
        tester = db.update(
            "beta_testers",
            existing[0]["id"],
            {
                "first_name": body.first_name.strip(),
                "device": body.device,
                "os_version": body.os_version,
                "app_version": body.app_version,
            },
        )
    else:
        tester = db.insert(
            "beta_testers",
            {
                "project_id": project["id"],
                "email": email,
                "first_name": body.first_name.strip(),
                "device": body.device,
                "os_version": body.os_version,
                "app_version": body.app_version,
            },
        )

    token = create_tester_token(tester["id"], project["id"])
    return {
        "tester_id": tester["id"],
        "token": token,
        "first_name": tester.get("first_name"),
        "project_name": project["name"],
        "app_version": tester.get("app_version") or latest_app_version(db, project["id"]),
    }


@router.post("/beta/feedback")
def beta_submit_feedback(
    body: BetaFeedbackRequest,
    auth: dict[str, str] = Depends(beta_tester_auth),
) -> dict[str, Any]:
    db = get_supabase()
    project = resolve_project_by_slug(db, body.project_slug)
    if auth["project_id"] != project["id"]:
        raise HTTPException(status_code=403, detail="Token non valide pour ce projet")

    tester = get_tester_or_404(db, auth["tester_id"])
    if tester["project_id"] != project["id"]:
        raise HTTPException(status_code=403, detail="Testeuse non inscrite à ce projet")

    screenshot_url: str | None = None
    if body.screenshot_base64:
        try:
            screenshot_url = upload_screenshot(db, body.screenshot_base64, project["id"])
        except Exception as exc:
            logger.exception("beta screenshot upload failed")
            raise HTTPException(status_code=400, detail="Échec upload screenshot") from exc

    ticket = create_feedback_ticket(
        db,
        project_id=project["id"],
        feedback_type=body.type,
        severity=body.severity,
        title=body.title.strip(),
        description=body.description.strip(),
        tester=tester,
    )

    feedback = db.insert(
        "beta_feedback",
        {
            "tester_id": tester["id"],
            "project_id": project["id"],
            "type": body.type,
            "title": body.title.strip(),
            "description": body.description.strip(),
            "screenshot_url": screenshot_url,
            "severity": body.severity,
            "ticket_id": ticket["id"],
        },
    )

    db.update(
        "beta_testers",
        tester["id"],
        {"feedback_count": int(tester.get("feedback_count") or 0) + 1},
    )

    return {"feedback_id": feedback["id"], "ticket_id": ticket["id"]}


@router.get("/beta/my-feedback")
def beta_my_feedback(
    auth: dict[str, str] = Depends(beta_tester_auth),
) -> list[dict[str, Any]]:
    db = get_supabase()
    return db.select(
        "beta_feedback",
        filters={"tester_id": auth["tester_id"]},
        order_by="created_at",
        ascending=False,
        limit=50,
    )


@router.get("/beta/testers")
def beta_list_testers(project_id: str | None = None) -> list[dict[str, Any]]:
    db = get_supabase()
    filters = {"project_id": project_id} if project_id else None
    testers = db.select(
        "beta_testers",
        filters=filters,
        order_by="joined_at",
        ascending=False,
    )
    projects = {p["id"]: p["name"] for p in db.select("projects")}
    for tester in testers:
        tester["project_name"] = projects.get(tester.get("project_id"), "")
    return testers


@router.get("/beta/testers/export")
def beta_export_testers(project_id: str | None = None) -> StreamingResponse:
    testers = beta_list_testers(project_id=project_id)
    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow([
        "prénom", "email", "projet", "appareil", "os", "version_app",
        "feedbacks", "inscription",
    ])
    for t in testers:
        writer.writerow([
            t.get("first_name") or "",
            t.get("email") or "",
            t.get("project_name") or "",
            t.get("device") or "",
            t.get("os_version") or "",
            t.get("app_version") or "",
            t.get("feedback_count") or 0,
            t.get("joined_at") or "",
        ])
    buffer.seek(0)
    return StreamingResponse(
        iter([buffer.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": 'attachment; filename="beta_testers.csv"'},
    )


@router.get("/beta/feedback")
def beta_list_feedback(
    project_id: str | None = None,
    tester_id: str | None = None,
) -> list[dict[str, Any]]:
    db = get_supabase()
    filters: dict[str, Any] = {}
    if project_id:
        filters["project_id"] = project_id
    if tester_id:
        filters["tester_id"] = tester_id

    feedback = db.select(
        "beta_feedback",
        filters=filters or None,
        order_by="created_at",
        ascending=False,
        limit=200,
    )

    testers = {t["id"]: t for t in db.select("beta_testers")}
    projects = {p["id"]: p["name"] for p in db.select("projects")}
    for row in feedback:
        tester = testers.get(row.get("tester_id"), {})
        row["tester_name"] = tester.get("first_name")
        row["tester_email"] = tester.get("email")
        row["project_name"] = projects.get(row.get("project_id"), "")
    return feedback


@router.get("/beta/stats")
def beta_stats(project_id: str | None = None) -> dict[str, Any]:
    db = get_supabase()
    tester_filters = {"project_id": project_id} if project_id else None
    feedback_filters = {"project_id": project_id} if project_id else None

    testers = db.select("beta_testers", filters=tester_filters)
    feedback = db.select("beta_feedback", filters=feedback_filters)

    week_ago = datetime.now(timezone.utc) - timedelta(days=7)
    feedback_this_week = 0
    by_type: dict[str, int] = {}
    by_severity: dict[str, int] = {}
    timeline: dict[str, int] = {}

    for row in feedback:
        created = row.get("created_at")
        if created:
            try:
                dt = datetime.fromisoformat(created.replace("Z", "+00:00"))
                if dt >= week_ago:
                    feedback_this_week += 1
                day_key = dt.date().isoformat()
                timeline[day_key] = timeline.get(day_key, 0) + 1
            except ValueError:
                pass

        fb_type = row.get("type") or "autre"
        by_type[fb_type] = by_type.get(fb_type, 0) + 1
        sev = row.get("severity") or "non_renseigné"
        by_severity[sev] = by_severity.get(sev, 0) + 1

    # Last 7 days timeline (fill gaps)
    timeline_7d: list[dict[str, Any]] = []
    today = datetime.now(timezone.utc).date()
    for i in range(6, -1, -1):
        day = today - timedelta(days=i)
        key = day.isoformat()
        timeline_7d.append({"date": key, "count": timeline.get(key, 0)})

    return {
        "total_testers": len(testers),
        "total_feedback": len(feedback),
        "feedback_this_week": feedback_this_week,
        "by_type": by_type,
        "by_severity": by_severity,
        "timeline_7d": timeline_7d,
    }


@router.post("/beta/invite")
def beta_invite(body: BetaInviteRequest) -> dict[str, str]:
    db = get_supabase()
    rows = db.select("projects", filters={"id": body.project_id})
    if not rows:
        raise HTTPException(status_code=404, detail="Projet introuvable")
    slug = project_slug_for(rows[0])
    return {"invite_url": invite_url_for_slug(slug), "project_slug": slug}


