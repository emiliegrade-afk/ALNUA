"""Auto-split from api/main.py — core routes."""

from __future__ import annotations

from api.route_common import *  # noqa: F403

router = APIRouter()


@router.get("/projects")
def list_projects(branch: str | None = None) -> list[dict[str, Any]]:
    db = get_supabase()
    filters = {"branch": branch} if branch else None
    return db.select("projects", filters=filters, order_by="name")


@router.get("/projects/{project_id}")
def get_project(project_id: str) -> dict[str, Any]:
    db = get_supabase()
    rows = db.select("projects", filters={"id": project_id})
    if not rows:
        raise HTTPException(status_code=404, detail="Project not found")
    return rows[0]


@router.post("/projects")
def create_project(body: ProjectCreate) -> dict[str, Any]:
    """Crée un projet ALNUA et son dossier brainstorm_notes/[slug]."""
    db = get_supabase()
    try:
        row = db.insert(
            "projects",
            {
                "name": body.name.strip(),
                "branch": body.branch,
                "description": body.description.strip(),
                "status": body.status,
            },
        )
        BrainstormAgent.ensure_project_notes_dir(row["name"], row["id"])
        return row
    except Exception as exc:
        msg = str(exc)
        if "row-level security" in msg.lower() or "42501" in msg:
            raise HTTPException(
                status_code=503,
                detail=(
                    "Supabase RLS bloque la création. Utilise la clé service_role "
                    "ou exécute database/fix_rls_dev.sql."
                ),
            ) from exc
        logger.exception("create_project failed")
        raise HTTPException(status_code=500, detail=msg) from exc


@router.post("/dev-log")
def create_dev_log(body: DevLogCreate) -> dict[str, Any]:
    db = get_supabase()
    row = db.insert(
        "dev_log",
        {
            "project_id": body.project_id,
            "content": body.content,
            "date": (body.log_date or date.today()).isoformat(),
        },
    )
    return row


@router.get("/dev-log")
def list_dev_log(project_id: str, unused_only: bool = False) -> list[dict[str, Any]]:
    db = get_supabase()
    filters: dict[str, Any] = {"project_id": project_id}
    if unused_only:
        filters["used_for_content"] = False
    return db.select("dev_log", filters=filters, order_by="date", ascending=False)


PRIORITY_ORDER = {"critical": 0, "high": 1, "medium": 2, "low": 3}


@router.post("/tickets")
def create_ticket(body: TicketCreate) -> dict[str, Any]:
    db = get_supabase()
    return db.insert(
        "tickets",
        {
            "project_id": body.project_id,
            "type": body.type,
            "priority": body.priority,
            "title": body.title,
            "description": body.description,
            "source": body.source,
            "status": "open",
        },
    )


@router.get("/tickets")
def list_tickets(
    project_id: str | None = None,
    status: str | None = None,
    priority: list[str] | None = Query(None),
    ticket_type: list[str] | None = Query(None, alias="type"),
    limit: int = Query(default=50, le=200),
) -> list[dict[str, Any]]:
    db = get_supabase()
    filters: dict[str, Any] = {}
    if project_id:
        filters["project_id"] = project_id
    if status:
        filters["status"] = status

    tickets = db.select(
        "tickets",
        filters=filters or None,
        order_by="created_at",
        ascending=False,
        limit=limit * 3,
    )

    if priority:
        allowed = set(priority)
        tickets = [t for t in tickets if t.get("priority") in allowed]
    if ticket_type:
        allowed_types = set(ticket_type)
        tickets = [t for t in tickets if t.get("type") in allowed_types]

    # Priorité critique d'abord, puis date desc (tri stable)
    tickets.sort(key=lambda t: t.get("created_at") or "", reverse=True)
    tickets.sort(key=lambda t: PRIORITY_ORDER.get(t.get("priority", "medium"), 9))

    projects = {p["id"]: p["name"] for p in db.select("projects")}
    for ticket in tickets[:limit]:
        ticket["project_name"] = projects.get(ticket.get("project_id"), "Projet")

    return tickets[:limit]


@router.patch("/tickets/{ticket_id}")
def update_ticket(ticket_id: str, body: TicketUpdate) -> dict[str, Any]:
    db = get_supabase()
    rows = db.select("tickets", filters={"id": ticket_id})
    if not rows:
        raise HTTPException(status_code=404, detail="Ticket not found")

    values = body.model_dump(exclude_none=True)
    if not values:
        raise HTTPException(status_code=400, detail="Aucun champ à mettre à jour")
    return db.update("tickets", ticket_id, values)


@router.patch("/tickets/{ticket_id}/status")
def update_ticket_status(ticket_id: str, status: str) -> dict[str, Any]:
    allowed = {"open", "in_progress", "done", "wont_fix"}
    if status not in allowed:
        raise HTTPException(status_code=400, detail=f"status must be one of {allowed}")
    db = get_supabase()
    return db.update("tickets", ticket_id, {"status": status})


@router.post("/tickets/{ticket_id}/generate-cursor-prompt")
def generate_ticket_cursor_prompt(ticket_id: str) -> dict[str, Any]:
    settings = get_settings()
    if not settings.openrouter_api_key.strip():
        raise HTTPException(status_code=503, detail="OPENROUTER_API_KEY manquante")
    agent = SpecAgent()
    try:
        updated = agent.generate_cursor_prompt(ticket_id)
        return {"cursor_prompt": updated.get("cursor_prompt", ""), "ticket": updated}
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except Exception as exc:
        logger.exception("generate_cursor_prompt failed")
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.post("/feedback")
def create_feedback(body: FeedbackCreate) -> dict[str, Any]:
    db = get_supabase()
    return db.insert(
        "feedback",
        {
            "project_id": body.project_id,
            "source": body.source,
            "content": body.content,
            "author": body.author,
            "rating": body.rating,
            "sentiment": body.sentiment,
            "status": "new",
        },
    )


@router.get("/feedback")
def list_feedback(
    project_id: str | None = None,
    status: str | None = None,
    limit: int = Query(default=50, le=200),
) -> list[dict[str, Any]]:
    db = get_supabase()
    filters: dict[str, Any] = {}
    if project_id:
        filters["project_id"] = project_id
    if status:
        filters["status"] = status
    rows = db.select(
        "feedback",
        filters=filters or None,
        order_by="created_at",
        ascending=False,
        limit=limit,
    )
    if rows and project_id is None:
        projects = {p["id"]: p["name"] for p in db.select("projects")}
        for row in rows:
            row["project_name"] = projects.get(row.get("project_id"), "Projet")
    return rows


ROADMAP_PRIORITY_ORDER = {"critical": 0, "high": 1, "medium": 2, "low": 3}
ROADMAP_STATUSES_ALLOWED = frozenset({"idea", "planned", "in_progress", "done"})


def _normalize_roadmap_row(row: dict[str, Any]) -> dict[str, Any]:
    """Map legacy DB values (int priority, sprint) to the v2 schema."""
    priority = row.get("priority", "medium")
    if isinstance(priority, (int, float)):
        n = int(priority)
        row["priority"] = (
            "critical" if n >= 8 else "high" if n >= 6 else "medium" if n >= 3 else "low"
        )
    elif isinstance(priority, str) and priority.isdigit():
        n = int(priority)
        row["priority"] = (
            "critical" if n >= 8 else "high" if n >= 6 else "medium" if n >= 3 else "low"
        )
    elif priority not in ROADMAP_PRIORITY_ORDER:
        row["priority"] = "medium"

    status = row.get("status", "planned")
    if status not in ROADMAP_STATUSES_ALLOWED:
        row["status"] = "planned"

    if not row.get("phase") and row.get("sprint"):
        row["phase"] = row["sprint"]

    return row


def _enrich_roadmap_items(
    db: Any, items: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    if not items:
        return items
    projects = {p["id"]: p["name"] for p in db.select("projects")}
    for row in items:
        _normalize_roadmap_row(row)
        row["project_name"] = projects.get(row.get("project_id"), "Projet")
    return items


def _sort_roadmap_items(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    # critical first, then earliest due_date (nulls last)
    items.sort(
        key=lambda r: r.get("due_date") or "9999-12-31",
    )
    items.sort(
        key=lambda r: ROADMAP_PRIORITY_ORDER.get(
            str(r.get("priority", "medium")), 9
        ),
    )
    return items


@router.get("/roadmap")
def list_roadmap(
    status: str | None = None,
    project_id: str | None = None,
    priority: list[str] | None = Query(None),
    phase: str | None = None,
) -> list[dict[str, Any]]:
    db = get_supabase()
    filters: dict[str, Any] = {}
    if status:
        filters["status"] = status
    if project_id:
        filters["project_id"] = project_id
    if phase:
        filters["phase"] = phase

    items = db.select(
        "roadmap",
        filters=filters or None,
        order_by="created_at",
        ascending=False,
    )

    if priority:
        allowed = set(priority)
        items = [r for r in items if r.get("priority") in allowed]

    return _enrich_roadmap_items(db, _sort_roadmap_items(items))


@router.post("/roadmap")
def create_roadmap_item(body: RoadmapCreate) -> dict[str, Any]:
    db = get_supabase()
    row = db.insert(
        "roadmap",
        {
            "project_id": body.project_id,
            "title": body.title,
            "description": body.description,
            "status": body.status,
            "priority": body.priority,
            "phase": body.phase or "",
            "due_date": body.due_date.isoformat() if body.due_date else None,
        },
    )
    return _enrich_roadmap_items(db, [row])[0]


@router.patch("/roadmap/{item_id}")
def update_roadmap_item(item_id: str, body: RoadmapUpdate) -> dict[str, Any]:
    db = get_supabase()
    rows = db.select("roadmap", filters={"id": item_id})
    if not rows:
        raise HTTPException(status_code=404, detail="Roadmap item not found")

    values = body.model_dump(exclude_none=True)
    if "due_date" in values and values["due_date"] is not None:
        values["due_date"] = values["due_date"].isoformat()
    if not values:
        raise HTTPException(status_code=400, detail="Aucun champ à mettre à jour")

    updated = db.update("roadmap", item_id, values)
    return _enrich_roadmap_items(db, [updated])[0]


@router.delete("/roadmap/{item_id}")
def delete_roadmap_item(item_id: str) -> dict[str, str]:
    db = get_supabase()
    rows = db.select("roadmap", filters={"id": item_id})
    if not rows:
        raise HTTPException(status_code=404, detail="Roadmap item not found")
    db.delete("roadmap", item_id)
    return {"status": "deleted", "id": item_id}


def _quick_capture_title(content: str, max_len: int = 120) -> str:
    """First non-empty line becomes the item title."""
    for line in content.strip().splitlines():
        stripped = line.strip()
        if stripped:
            return stripped[:max_len]
    return "Capture rapide"


@router.post("/quick-capture")
def quick_capture(body: QuickCaptureRequest) -> dict[str, Any]:
    """Route a Quick Capture payload to tickets, brainstorm, roadmap, or quick_notes."""
    db = get_supabase()
    content = body.content.strip()
    if not content:
        raise HTTPException(status_code=400, detail="Le contenu ne peut pas être vide")

    title = _quick_capture_title(content)
    priority = body.priority or "medium"

    if body.type == "ticket":
        row = db.insert(
            "tickets",
            {
                "project_id": body.project_id,
                "type": "bug",
                "priority": priority,
                "title": title,
                "description": content,
                "source": "quick_capture",
                "status": "open",
            },
        )
        return {
            "id": row["id"],
            "type": "ticket",
            "redirect_url": f"/tickets?id={row['id']}",
        }

    if body.type == "idea":
        capture_id = str(uuid.uuid4())
        row = db.insert(
            "brainstorm_summaries",
            {
                "project_id": body.project_id,
                "session_id": f"quick-capture-{capture_id}",
                "session_number": 0,
                "title": title,
                "summary": content,
                "key_ideas": [title],
            },
        )
        return {
            "id": row["id"],
            "type": "idea",
            "redirect_url": "/brainstorm",
        }

    if body.type == "roadmap":
        roadmap_row: dict[str, Any] = {
            "project_id": body.project_id,
            "title": title,
            "description": content,
            "status": "idea",
            "priority": priority,
        }
        if body.phase:
            roadmap_row["phase"] = body.phase
        if body.due_date:
            roadmap_row["due_date"] = body.due_date.isoformat()
        row = db.insert("roadmap", roadmap_row)
        return {
            "id": row["id"],
            "type": "roadmap",
            "redirect_url": f"/roadmap?id={row['id']}",
        }

    if body.type == "note":
        row = db.insert(
            "quick_notes",
            {
                "project_id": body.project_id,
                "content": content,
            },
        )
        return {
            "id": row["id"],
            "type": "note",
            "redirect_url": "/",
        }

    raise HTTPException(status_code=400, detail=f"Type inconnu : {body.type}")


@router.post("/roadmap/from-ticket/{ticket_id}")
def create_roadmap_from_ticket(ticket_id: str) -> dict[str, Any]:
    db = get_supabase()
    tickets = db.select("tickets", filters={"id": ticket_id})
    if not tickets:
        raise HTTPException(status_code=404, detail="Ticket not found")
    ticket = tickets[0]

    existing = db.select(
        "roadmap",
        filters={"linked_ticket_id": ticket_id},
    )
    if existing:
        raise HTTPException(
            status_code=409,
            detail="Un item roadmap existe déjà pour ce ticket",
        )

    priority = ticket.get("priority", "medium")
    if priority not in ROADMAP_PRIORITY_ORDER:
        priority = "medium"

    row = db.insert(
        "roadmap",
        {
            "project_id": ticket["project_id"],
            "title": ticket["title"],
            "description": ticket.get("description", ""),
            "status": "planned",
            "priority": priority,
            "linked_ticket_id": ticket_id,
        },
    )
    return _enrich_roadmap_items(db, [row])[0]


@router.get("/posts")
def list_posts(
    project_id: str | None = None,
    rnd_dossier_id: str | None = None,
    status: str | None = None,
    platform: str | None = None,
) -> list[dict[str, Any]]:
    db = get_supabase()
    filters: dict[str, Any] = {}
    if project_id:
        filters["project_id"] = project_id
    if rnd_dossier_id:
        filters["rnd_dossier_id"] = rnd_dossier_id
    if status:
        filters["status"] = status
    if platform:
        filters["platform"] = platform
    return db.select(
        "posts_queue",
        filters=filters or None,
        order_by="created_at",
        ascending=False,
    )


@router.patch("/posts/{post_id}")
def update_post(post_id: str, body: PostUpdate) -> dict[str, Any]:
    agent = ContentAgent()
    try:
        payload = body.model_dump(exclude_none=True)
        return agent.update_post(post_id, payload)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.patch("/posts/{post_id}/approve")
def approve_post(post_id: str) -> dict[str, Any]:
    agent = ContentAgent()
    return agent.approve_post(post_id)


def _fetch_all_analytics(db, project_id: str | None = None) -> list[dict[str, Any]]:
    filters = {"project_id": project_id} if project_id else None
    return db.select(
        "analytics",
        filters=filters,
        order_by="date",
        ascending=True,
        limit=2000,
    )


def _fetch_transactions(db, project_id: str | None = None) -> list[dict[str, Any]]:
    filters = {"project_id": project_id} if project_id else None
    return db.select(
        "transactions",
        filters=filters,
        order_by="date",
        ascending=True,
        limit=2000,
    )


def _kpi_metric(
    rows: list[dict[str, Any]],
    metric_name: str,
    project_id: str | None,
    use_sum_in_month: bool = False,
) -> dict[str, Any]:
    """Calcule valeur du mois courant + variation vs mois précédent."""
    cur_start, cur_end = month_bounds()
    prev_start, prev_end = previous_month_bounds()

    if use_sum_in_month:
        current = sum_metric_in_range(rows, metric_name, cur_start, cur_end, project_id)
        previous = sum_metric_in_range(rows, metric_name, prev_start, prev_end, project_id)
    else:
        cur_latest = latest_values_by_project(rows, metric_name, cur_end)
        prev_latest = latest_values_by_project(rows, metric_name, prev_end)
        if project_id:
            current = cur_latest.get(project_id)
            previous = prev_latest.get(project_id)
        else:
            current = sum(cur_latest.values()) if cur_latest else None
            previous = sum(prev_latest.values()) if prev_latest else None

    return {
        "value": current if current is not None else None,
        "change_pct": pct_change(current, previous),
    }


@router.get("/analytics")
def list_analytics(
    project_id: str | None = None,
    metric_name: str | None = None,
    period: str = Query(default="30d"),
    start_date: date | None = None,
    end_date: date | None = None,
) -> list[dict[str, Any]]:
    db = get_supabase()
    if start_date and end_date:
        start, end = start_date, end_date
    else:
        start, end = parse_period(period)

    rows = _fetch_all_analytics(db, project_id)
    if metric_name:
        rows = [r for r in rows if r.get("metric_name") == metric_name]
    rows = filter_by_date_range(rows, start, end)

    projects = {p["id"]: p["name"] for p in db.select("projects")}
    for row in rows:
        row["project_name"] = projects.get(row.get("project_id"), "Projet")
    return rows


@router.get("/analytics/summary")
def analytics_summary(project_id: str | None = None) -> dict[str, Any]:
    db = get_supabase()
    rows = _fetch_all_analytics(db, project_id)
    tx_rows = _fetch_transactions(db, project_id)

    cur_start, cur_end = month_bounds()
    prev_start, prev_end = previous_month_bounds()

    revenue_cur = sum(
        float(t["amount"])
        for t in tx_rows
        if t.get("type") in ("revenue", "income")
        and cur_start <= date.fromisoformat(str(t["date"])[:10]) <= cur_end
    )
    revenue_prev = sum(
        float(t["amount"])
        for t in tx_rows
        if t.get("type") in ("revenue", "income")
        and prev_start <= date.fromisoformat(str(t["date"])[:10]) <= prev_end
    )

    return {
        "downloads": _kpi_metric(rows, "downloads", project_id, use_sum_in_month=True),
        "subscriptions": _kpi_metric(rows, "subscriptions", project_id),
        "mrr": _kpi_metric(rows, "mrr", project_id),
        "churn": _kpi_metric(rows, "churn", project_id),
        "web_visitors": _kpi_metric(rows, "web_visitors", project_id, use_sum_in_month=True),
        "revenue_month": {
            "value": revenue_cur if revenue_cur else None,
            "change_pct": pct_change(revenue_cur, revenue_prev),
        },
    }


@router.get("/analytics/revenue")
def analytics_revenue(
    project_id: str | None = None,
    period: str = Query(default="30d"),
) -> dict[str, Any]:
    db = get_supabase()
    start, end = parse_period(period)
    tx_rows = filter_by_date_range(_fetch_transactions(db, project_id), start, end)
    analytics_rows = filter_by_date_range(_fetch_all_analytics(db, project_id), start, end)

    months: dict[str, dict[str, float]] = {}

    for tx in tx_rows:
        d = date.fromisoformat(str(tx["date"])[:10])
        key = d.strftime("%Y-%m")
        bucket = months.setdefault(key, {"revenue": 0.0, "expense": 0.0, "mrr": 0.0})
        if tx.get("type") in ("revenue", "income"):
            bucket["revenue"] += float(tx["amount"])
        else:
            bucket["expense"] += float(tx["amount"])

    for row in analytics_rows:
        if row.get("metric_name") != "mrr":
            continue
        d = date.fromisoformat(str(row["date"])[:10])
        key = d.strftime("%Y-%m")
        bucket = months.setdefault(key, {"revenue": 0.0, "expense": 0.0, "mrr": 0.0})
        bucket["mrr"] = max(bucket["mrr"], float(row["value"]))

    series = [
        {"month": k, **v}
        for k, v in sorted(months.items())
    ]
    return {"months": series}


@router.post("/analytics")
def create_analytics_metric(body: AnalyticsCreate) -> dict[str, Any]:
    db = get_supabase()
    return db.insert(
        "analytics",
        {
            "project_id": body.project_id,
            "metric_name": body.metric_name,
            "value": body.value,
            "date": (body.record_date or date.today()).isoformat(),
            "source": body.source,
        },
    )


@router.post("/transactions")
def create_transaction(body: TransactionCreate) -> dict[str, Any]:
    db = get_supabase()
    tx_type = "income" if body.type == "revenue" else body.type
    return db.insert(
        "transactions",
        {
            "project_id": body.project_id,
            "type": tx_type,
            "amount": body.amount,
            "currency": body.currency,
            "category": body.category,
            "description": body.description,
            "date": (body.transaction_date or date.today()).isoformat(),
            "is_recurring": body.is_recurring,
            "recurrence": body.recurrence,
        },
    )


@router.post("/faq")
def create_faq(body: FAQCreate) -> dict[str, Any]:
    bot = SAVBot()
    return bot.add_faq_entry(body.project_id, body.question, body.answer, body.tags)


@router.get("/faq")
def list_faq(project_id: str) -> list[dict[str, Any]]:
    bot = SAVBot()
    return bot.get_faq(project_id)


@router.post("/sav/ask")
def sav_ask(body: SAVQuestion) -> dict[str, Any]:
    bot = SAVBot()
    return bot.handle_question(body.project_id, body.question, body.author)


