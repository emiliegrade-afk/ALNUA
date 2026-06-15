"""GDD manager routes — gaming design document chunking (Phase 3)."""

from __future__ import annotations

from api.route_common import *  # noqa: F403

router = APIRouter(tags=["gdd"])


def _require_gdd_enabled() -> None:
    from config.settings import get_settings

    if not get_settings().gdd_manager_enabled:
        raise HTTPException(
            status_code=404,
            detail="GDD manager disabled — set GDD_MANAGER_ENABLED=1",
        )


@router.post("/gdd/ingest")
async def gdd_ingest(
    project_id: str = Form(...),
    document_title: str = Form(default="GDD"),
    replace_existing: bool = Form(default=True),
    file: UploadFile | None = File(default=None),
    markdown: str | None = Form(default=None),
) -> dict[str, Any]:
    """
    Ingest a GDD markdown file or raw text for a gaming project.
    Replaces existing chunks by default.
    """
    _require_gdd_enabled()

    if file is None and not (markdown and markdown.strip()):
        raise HTTPException(status_code=400, detail="Provide file or markdown text")

    if file is not None:
        filename = file.filename or "gdd.md"
        if not filename.lower().endswith((".md", ".markdown", ".txt")):
            raise HTTPException(
                status_code=400,
                detail="v1 supports markdown/text only (.md, .markdown, .txt)",
            )
        raw = (await file.read()).decode("utf-8", errors="replace")
        source_filename = filename
    else:
        raw = markdown or ""
        source_filename = None

    from services.gdd_manager import ingest_gdd

    db = get_supabase()
    try:
        return ingest_gdd(
            db,
            project_id=project_id,
            markdown=raw,
            document_title=document_title.strip() or "GDD",
            source_filename=source_filename,
            replace_existing=replace_existing,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        logger.exception("gdd_ingest failed")
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.get("/gdd/{project_id}/sections")
def gdd_sections(project_id: str) -> list[dict[str, Any]]:
    """List GDD sections with chunk counts for a project."""
    _require_gdd_enabled()
    from services.gdd_manager import list_gdd_sections

    return list_gdd_sections(get_supabase(), project_id)


@router.get("/gdd/{project_id}/chunks")
def gdd_chunks(
    project_id: str,
    section: str | None = Query(default=None),
    limit: int = Query(default=100, ge=1, le=200),
) -> list[dict[str, Any]]:
    """Return stored chunks, optionally filtered by section."""
    _require_gdd_enabled()
    from services.gdd_manager import list_gdd_chunks

    return list_gdd_chunks(
        get_supabase(),
        project_id,
        section_title=section,
        limit=limit,
    )


@router.get("/gdd/{project_id}/search")
def gdd_search(
    project_id: str,
    q: str = Query(..., min_length=2),
    limit: int = Query(default=20, ge=1, le=50),
) -> dict[str, Any]:
    """Full-text substring search across GDD chunks (v1)."""
    _require_gdd_enabled()
    from services.gdd_manager import search_gdd_chunks

    results = search_gdd_chunks(get_supabase(), project_id, q, limit=limit)
    return {"query": q, "count": len(results), "results": results}


@router.delete("/gdd/{project_id}")
def gdd_delete_project_chunks(project_id: str) -> dict[str, Any]:
    """Remove all GDD chunks for a project."""
    _require_gdd_enabled()
    db = get_supabase()
    try:
        db.table("gdd_chunks").delete().eq("project_id", project_id).execute()
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    return {"deleted": True, "project_id": project_id}
