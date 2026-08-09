"""Hub CRUD — peeled from core.py (debt paydown)."""

from __future__ import annotations

from api.route_common import *  # noqa: F403

router = APIRouter()

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


