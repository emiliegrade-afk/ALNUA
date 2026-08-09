"""Hub CRUD — peeled from core.py (debt paydown)."""

from __future__ import annotations

from api.route_common import *  # noqa: F403

router = APIRouter()

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


@router.post("/posts")
def create_post(body: PostCreate) -> dict[str, Any]:
    """Création manuelle (Composer Studio) — écrite/éditée par un humain ou un agent secteur."""
    from skills.skill_social_scheduler import queue_post

    result = queue_post(
        project_id=body.project_id,
        platform=body.platform,
        content=body.text_content,
        sector=body.sector or "",
        author_agent=body.author_agent_id or "",
        content_type=body.content_type,
        hashtags=body.hashtags,
        layout=body.layout,
        media_urls=body.media_urls,
        channel=body.channel or "",
        scheduled_for=body.scheduled_at,
        status=body.status,
        db=get_supabase(),
    )
    if not result.get("ok"):
        raise HTTPException(status_code=400, detail=result.get("error", "Création impossible"))
    return result["post"]


@router.get("/content/calendar")
def content_calendar(
    date_from: str,
    date_to: str,
    sector: str | None = None,
) -> dict[str, Any]:
    """Vue calendrier transverse (Studio Typefully) : posts planifiés entre deux dates, par jour."""
    from skills.skill_social_scheduler import get_calendar

    if sector and sector not in {"app", "gaming", "robo", "company"}:
        raise HTTPException(status_code=400, detail=f"Secteur invalide : {sector}")
    return get_calendar(date_from, date_to, sector=sector or "", db=get_supabase())


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


