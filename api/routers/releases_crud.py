"""Release notes CRUD routes."""

from __future__ import annotations

from api.route_common import *  # noqa: F403
from api.routers.releases_helpers import enrich_releases_with_project_names

router = APIRouter()


@router.get("/releases")
def list_releases(project_id: str | None = None) -> list[dict[str, Any]]:
    db = get_supabase()
    try:
        query = db.table("releases").select("*").order("created_at", desc=True)
        if project_id:
            query = query.eq("project_id", project_id)
        response = query.execute()
        return enrich_releases_with_project_names(db, response.data or [])
    except Exception as exc:
        msg = str(exc)
        if "releases" in msg and ("PGRST205" in msg or "schema cache" in msg):
            logger.warning("releases table missing — returning empty list")
            return []
        logger.exception("list_releases failed")
        raise HTTPException(status_code=500, detail="Impossible de charger les releases") from exc


@router.post("/releases/generate")
def generate_release(body: ReleaseGenerateRequest) -> dict[str, Any]:
    result = generate_release_notes(
        project_id=body.project_id,
        version=body.version.strip(),
        since_date=body.since_date,
        dev_log_ids=body.dev_log_ids,
    )
    db = get_supabase()
    enriched = enrich_releases_with_project_names(db, [result["release"]])
    return enriched[0]


@router.get("/releases/generate")
def get_release_generate_not_allowed() -> None:
    """Static path before {release_id} — avoid treating 'generate' as a UUID."""
    raise HTTPException(
        status_code=405,
        detail="Utiliser POST /releases/generate",
    )


@router.get("/releases/{release_id}")
def get_release(release_id: str) -> dict[str, Any]:
    db = get_supabase()
    rows = db.select("releases", filters={"id": release_id})
    if not rows:
        raise HTTPException(status_code=404, detail="Release introuvable")
    enriched = enrich_releases_with_project_names(db, rows)
    return enriched[0]


@router.patch("/releases/{release_id}")
def update_release(release_id: str, body: ReleaseUpdate) -> dict[str, Any]:
    db = get_supabase()
    existing = db.select("releases", filters={"id": release_id})
    if not existing:
        raise HTTPException(status_code=404, detail="Release introuvable")

    updates = body.model_dump(exclude_none=True)
    if not updates:
        raise HTTPException(status_code=400, detail="Aucune modification fournie")
    if "release_date" in updates and updates["release_date"] is not None:
        updates["release_date"] = updates["release_date"].isoformat()

    row = db.update("releases", release_id, updates)
    enriched = enrich_releases_with_project_names(db, [row])
    return enriched[0]


@router.delete("/releases/{release_id}")
def delete_release(release_id: str) -> dict[str, bool]:
    db = get_supabase()
    existing = db.select("releases", filters={"id": release_id})
    if not existing:
        raise HTTPException(status_code=404, detail="Release introuvable")
    db.delete("releases", release_id)
    return {"ok": True}
