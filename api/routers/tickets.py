"""Hub CRUD — peeled from core.py (debt paydown)."""

from __future__ import annotations

from api.route_common import *  # noqa: F403

router = APIRouter()

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
            "assignee_agent_id": body.assignee_agent_id,
            "story_points": body.story_points,
            "due_date": body.due_date.isoformat() if body.due_date else None,
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
    if "due_date" in values and values["due_date"] is not None:
        values["due_date"] = values["due_date"].isoformat()
    if not values:
        raise HTTPException(status_code=400, detail="Aucun champ à mettre à jour")
    return db.update("tickets", ticket_id, values)


@router.patch("/tickets/{ticket_id}/status")
def update_ticket_status(ticket_id: str, status: str) -> dict[str, Any]:
    allowed = {"open", "in_progress", "in_review", "done", "wont_fix"}
    if status not in allowed:
        raise HTTPException(status_code=400, detail=f"status must be one of {allowed}")
    db = get_supabase()
    rows = db.select("tickets", filters={"id": ticket_id})
    if not rows:
        raise HTTPException(status_code=404, detail="Ticket not found")
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


