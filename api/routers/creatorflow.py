"""CreatorFlow product API — assets, calendar, exports (Sprint 0–4)."""

from __future__ import annotations

import uuid

from fastapi import BackgroundTasks

from api.route_common import *  # noqa: F403
from agents.cf_timing_optimizer import get_cf_timing_suggestions
from services.creatorflow_export_runner import (
    analyze_and_persist_asset,
    count_user_exports_today,
    run_cf_export,
)
from services.creatorflow_platforms import (
    disconnect_cf_platform,
    list_cf_platform_status,
    start_cf_platform_connect,
    sync_cf_platform_connection,
)
from services.creatorflow_storage import (
    enrich_asset_row,
    infer_file_type,
    upload_cf_asset_file,
)
from services.creatorflow_media import probe_media_bytes
from services.creatorflow_projects import (
    create_cf_project,
    ensure_default_cf_project,
    get_cf_project,
    list_cf_projects,
    resolve_cf_project_id,
)
from services.creatorflow_stats import get_cf_export_stats
from services.creatorflow_ideas import (
    create_cf_idea,
    delete_cf_idea,
    get_cf_idea,
    list_cf_ideas,
    update_cf_idea,
)
from services.creatorflow_dna import list_cf_creator_dna, upsert_cf_creator_dna
from services.creatorflow_user_ai import (
    delete_cf_ai_settings,
    get_cf_ai_settings,
    upsert_cf_ai_settings,
)
from services.creatorflow_brainstorm import (
    brainstorm_on_idea,
    generate_script_for_idea,
    generate_shot_list_for_idea,
    list_idea_artifacts,
    list_idea_messages,
)
from services.creatorflow_pipeline import (
    get_idea_pipeline,
    link_asset_to_idea,
    schedule_idea_to_calendar,
)
from services.studio.flow_runner import run_studio_flow
from services.studio.flows import (
    create_studio_flow,
    delete_studio_flow,
    get_studio_flow,
    list_studio_flows_for_idea,
    update_studio_flow,
)
from services.studio.templates import get_studio_templates
from services.studio import (
    create_studio_job,
    enrich_studio_job,
    enrich_studio_jobs,
    get_studio_catalog,
    get_studio_job,
    link_studio_job_asset,
    list_studio_jobs_for_idea,
    run_studio_job,
)
from database.creatorflow_supabase_client import cf_supabase_configured, get_cf_supabase
from config.settings import get_settings

router = APIRouter(prefix="/creatorflow", tags=["creatorflow"])

_CF_ASSETS = "cf_assets"
_CF_CALENDAR = "cf_calendar_entries"
_CF_EXPORTS = "cf_exports"
_CF_PLATFORMS = "cf_platform_connections"
_CF_PROJECTS = "cf_projects"


def _require_cf_user_id(x_user_id: str | None = Header(default=None, alias="X-User-Id")) -> str:
    raw = (x_user_id or "").strip()
    if not raw:
        raise HTTPException(status_code=400, detail="Header X-User-Id requis")
    try:
        uuid.UUID(raw)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="X-User-Id doit être un UUID") from exc
    return raw


def _strip_suggestion_source(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {k: v for k, v in item.items() if k != "source"}
        for item in items
    ]


@router.get("/health")
def creatorflow_health() -> dict[str, str]:
    return {
        "status": "ok",
        "service": "creatorflow",
        "sprint": "studio-v3",
        "db_configured": str(cf_supabase_configured()).lower(),
    }


# ---------------------------------------------------------------------------
# Projects (P1)
# ---------------------------------------------------------------------------


@router.get("/projects", response_model=list[CfProjectOut])
def list_cf_projects_route(user_id: str = Depends(_require_cf_user_id)) -> list[dict[str, Any]]:
    return list_cf_projects(user_id)


@router.post("/projects", response_model=CfProjectOut, status_code=201)
def create_cf_project_route(
    body: CfProjectCreate,
    user_id: str = Depends(_require_cf_user_id),
) -> dict[str, Any]:
    return create_cf_project(user_id, body.name, body.description)


@router.get("/projects/{project_id}", response_model=CfProjectOut)
def get_cf_project_route(
    project_id: str,
    user_id: str = Depends(_require_cf_user_id),
) -> dict[str, Any]:
    project = get_cf_project(project_id, user_id)
    if not project:
        raise HTTPException(status_code=404, detail="Projet introuvable")
    return project


# ---------------------------------------------------------------------------
# Assets
# ---------------------------------------------------------------------------


@router.get("/assets", response_model=list[CfAssetOut])
def list_cf_assets(
    user_id: str = Depends(_require_cf_user_id),
    project_id: str | None = Query(default=None),
) -> list[dict[str, Any]]:
    db = get_cf_supabase()
    filters: dict[str, Any] = {"user_id": user_id}
    if project_id:
        filters["project_id"] = project_id
    rows = db.select(
        _CF_ASSETS,
        filters=filters,
        order_by="created_at",
        ascending=False,
    )
    return [enrich_asset_row(db, row) for row in rows]


@router.post("/assets", response_model=CfAssetOut, status_code=201)
def create_cf_asset(
    body: CfAssetCreate,
    background_tasks: BackgroundTasks,
    user_id: str = Depends(_require_cf_user_id),
) -> dict[str, Any]:
    db = get_cf_supabase()
    try:
        resolved_project = resolve_cf_project_id(user_id, body.project_id, db)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    row = db.insert(
        _CF_ASSETS,
        {
            **body.model_dump(exclude_none=True),
            "user_id": user_id,
            "project_id": resolved_project,
            "status": "pending",
        },
    )
    background_tasks.add_task(analyze_and_persist_asset, row["id"], user_id, db)
    return enrich_asset_row(db, row)


@router.post("/assets/upload", response_model=CfAssetOut, status_code=201)
async def upload_cf_asset(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    title: str | None = Form(default=None),
    project_id: str | None = Form(default=None),
    user_id: str = Depends(_require_cf_user_id),
) -> dict[str, Any]:
    db = get_cf_supabase()
    mime = (file.content_type or "application/octet-stream").split(";")[0].strip()
    content = await file.read()
    if not content:
        raise HTTPException(status_code=400, detail="Fichier vide")

    try:
        resolved_project = resolve_cf_project_id(user_id, project_id, db)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    try:
        storage_path = upload_cf_asset_file(
            db,
            user_id,
            content,
            file.filename or "asset",
            mime,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        logger.exception("cf asset upload failed")
        raise HTTPException(status_code=500, detail="Échec upload Storage") from exc

    probe = probe_media_bytes(content, mime, filename=file.filename or "asset")
    duration = probe.get("duration_seconds")

    asset_title = (title or file.filename or "Sans titre").strip()[:500]
    row = db.insert(
        _CF_ASSETS,
        {
            "user_id": user_id,
            "project_id": resolved_project,
            "title": asset_title,
            "file_url": storage_path,
            "file_type": infer_file_type(mime),
            "file_size_bytes": len(content),
            "duration_seconds": duration,
            "mime_type": mime,
            "status": "pending",
            "metadata": {"original_filename": file.filename or "", **probe},
        },
    )
    background_tasks.add_task(analyze_and_persist_asset, row["id"], user_id, db)
    return enrich_asset_row(db, row)


@router.post("/assets/{asset_id}/analyze", response_model=CfAssetOut)
def reanalyze_cf_asset(
    asset_id: str,
    background_tasks: BackgroundTasks,
    user_id: str = Depends(_require_cf_user_id),
) -> dict[str, Any]:
    db = get_cf_supabase()
    rows = db.select(_CF_ASSETS, filters={"id": asset_id, "user_id": user_id}, limit=1)
    if not rows:
        raise HTTPException(status_code=404, detail="Asset introuvable")
    db.update(_CF_ASSETS, asset_id, {"status": "pending"})
    background_tasks.add_task(analyze_and_persist_asset, asset_id, user_id, db)
    return enrich_asset_row(db, {**rows[0], "status": "pending"})


@router.get("/assets/{asset_id}", response_model=CfAssetOut)
def get_cf_asset(
    asset_id: str,
    user_id: str = Depends(_require_cf_user_id),
) -> dict[str, Any]:
    db = get_cf_supabase()
    rows = db.select(_CF_ASSETS, filters={"id": asset_id, "user_id": user_id}, limit=1)
    if not rows:
        raise HTTPException(status_code=404, detail="Asset introuvable")
    return enrich_asset_row(db, rows[0])


@router.delete("/assets/{asset_id}", status_code=204)
def delete_cf_asset(
    asset_id: str,
    user_id: str = Depends(_require_cf_user_id),
) -> None:
    db = get_cf_supabase()
    existing = db.select(_CF_ASSETS, filters={"id": asset_id, "user_id": user_id}, limit=1)
    if not existing:
        raise HTTPException(status_code=404, detail="Asset introuvable")
    db.delete(_CF_ASSETS, asset_id)


# ---------------------------------------------------------------------------
# Calendar
# ---------------------------------------------------------------------------


@router.get("/calendar", response_model=list[CfCalendarEntryOut])
def list_cf_calendar(
    user_id: str = Depends(_require_cf_user_id),
    project_id: str | None = Query(default=None),
) -> list[dict[str, Any]]:
    db = get_cf_supabase()
    filters: dict[str, Any] = {"user_id": user_id}
    if project_id:
        filters["project_id"] = project_id
    return db.select(
        _CF_CALENDAR,
        filters=filters,
        order_by="scheduled_at",
        ascending=True,
    )


@router.post("/calendar", response_model=CfCalendarEntryOut, status_code=201)
def create_cf_calendar_entry(
    body: CfCalendarEntryCreate,
    user_id: str = Depends(_require_cf_user_id),
) -> dict[str, Any]:
    db = get_cf_supabase()
    try:
        resolved_project = resolve_cf_project_id(user_id, body.project_id, db)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    payload = body.model_dump(exclude_none=True)
    payload["project_id"] = resolved_project
    if payload.get("asset_id"):
        asset_rows = db.select(
            _CF_ASSETS,
            filters={"id": payload["asset_id"], "user_id": user_id},
            limit=1,
        )
        if not asset_rows:
            raise HTTPException(status_code=400, detail="Asset lié introuvable")
    payload["user_id"] = user_id
    payload["scheduled_at"] = body.scheduled_at.isoformat()
    if payload.get("asset_id"):
        payload["asset_id"] = str(payload["asset_id"])
    return db.insert(_CF_CALENDAR, payload)


@router.patch("/calendar/{entry_id}", response_model=CfCalendarEntryOut)
def update_cf_calendar_entry(
    entry_id: str,
    body: CfCalendarEntryUpdate,
    user_id: str = Depends(_require_cf_user_id),
) -> dict[str, Any]:
    db = get_cf_supabase()
    existing = db.select(
        _CF_CALENDAR,
        filters={"id": entry_id, "user_id": user_id},
        limit=1,
    )
    if not existing:
        raise HTTPException(status_code=404, detail="Entrée calendrier introuvable")
    if existing[0].get("status") == "exported":
        raise HTTPException(status_code=400, detail="Publication déjà exportée — métadonnées verrouillées")

    payload = body.model_dump(exclude_none=True)
    if not payload:
        raise HTTPException(status_code=400, detail="Aucune modification fournie")
    if payload.get("scheduled_at") is not None:
        payload["scheduled_at"] = body.scheduled_at.isoformat()  # type: ignore[union-attr]
    return db.update(_CF_CALENDAR, entry_id, payload)


@router.delete("/calendar/{entry_id}", status_code=204)
def delete_cf_calendar_entry(
    entry_id: str,
    user_id: str = Depends(_require_cf_user_id),
) -> None:
    db = get_cf_supabase()
    existing = db.select(
        _CF_CALENDAR,
        filters={"id": entry_id, "user_id": user_id},
        limit=1,
    )
    if not existing:
        raise HTTPException(status_code=404, detail="Entrée calendrier introuvable")
    db.delete(_CF_CALENDAR, entry_id)


@router.get("/calendar/suggestions", response_model=list[CfTimingSuggestion])
def get_cf_calendar_suggestions(
    platform: str = Query(..., description="youtube | instagram"),
    user_id: str = Depends(_require_cf_user_id),
) -> list[dict[str, Any]]:
    if platform not in ("youtube", "instagram"):
        raise HTTPException(status_code=400, detail="Plateforme invalide")
    db = get_cf_supabase()
    raw = get_cf_timing_suggestions(user_id, platform, db)
    return _strip_suggestion_source(raw)


# ---------------------------------------------------------------------------
# Exports (Sprint 2 — mock publish)
# ---------------------------------------------------------------------------


@router.get("/exports", response_model=list[CfExportOut])
def list_cf_exports(user_id: str = Depends(_require_cf_user_id)) -> list[dict[str, Any]]:
    db = get_cf_supabase()
    return db.select(
        _CF_EXPORTS,
        filters={"user_id": user_id},
        order_by="created_at",
        ascending=False,
    )


@router.post("/exports", response_model=CfExportOut, status_code=201)
def trigger_cf_export(
    body: CfExportCreate,
    background_tasks: BackgroundTasks,
    user_id: str = Depends(_require_cf_user_id),
) -> dict[str, Any]:
    db = get_cf_supabase()
    entry_rows = db.select(
        _CF_CALENDAR,
        filters={"id": body.calendar_entry_id, "user_id": user_id},
        limit=1,
    )
    if not entry_rows:
        raise HTTPException(status_code=404, detail="Entrée calendrier introuvable")
    if entry_rows[0].get("platform") != body.platform:
        raise HTTPException(status_code=400, detail="Plateforme incompatible avec l'entrée calendrier")

    settings = get_settings()
    daily_count = count_user_exports_today(db, user_id)
    if daily_count >= settings.cf_export_daily_limit:
        raise HTTPException(
            status_code=429,
            detail=f"Limite quotidienne atteinte ({settings.cf_export_daily_limit} exports/jour)",
        )

    export_row = db.insert(
        _CF_EXPORTS,
        {
            "user_id": user_id,
            "calendar_entry_id": body.calendar_entry_id,
            "platform": body.platform,
            "status": "pending",
        },
    )
    background_tasks.add_task(run_cf_export, export_row["id"], user_id, db)
    return export_row


@router.get("/exports/{export_id}", response_model=CfExportOut)
def get_cf_export(
    export_id: str,
    user_id: str = Depends(_require_cf_user_id),
) -> dict[str, Any]:
    db = get_cf_supabase()
    rows = db.select(_CF_EXPORTS, filters={"id": export_id, "user_id": user_id}, limit=1)
    if not rows:
        raise HTTPException(status_code=404, detail="Export introuvable")
    return rows[0]


# ---------------------------------------------------------------------------
# Platforms (Sprint 3 — Composio OAuth)
# ---------------------------------------------------------------------------


@router.get("/platforms", response_model=list[CfPlatformConnectionOut])
def list_cf_platforms(user_id: str = Depends(_require_cf_user_id)) -> list[dict[str, Any]]:
    return list_cf_platform_status(user_id)


@router.post("/platforms/connect", response_model=CfPlatformConnectOut)
def connect_cf_platform(
    body: CfPlatformConnectRequest,
    user_id: str = Depends(_require_cf_user_id),
) -> dict[str, Any]:
    try:
        return start_cf_platform_connect(body.platform, user_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


@router.post("/platforms/sync", response_model=list[CfPlatformConnectionOut])
def sync_cf_platforms(
    platform: str | None = Query(default=None, description="youtube | instagram — omit for both"),
    user_id: str = Depends(_require_cf_user_id),
) -> list[dict[str, Any]]:
    if platform:
        if platform not in ("youtube", "instagram"):
            raise HTTPException(status_code=400, detail="Plateforme invalide")
        return [sync_cf_platform_connection(user_id, platform)]
    return list_cf_platform_status(user_id)


@router.delete("/platforms/{platform}", response_model=CfPlatformConnectionOut)
def disconnect_cf_platform_route(
    platform: str,
    user_id: str = Depends(_require_cf_user_id),
) -> dict[str, Any]:
    if platform not in ("youtube", "instagram"):
        raise HTTPException(status_code=400, detail="Plateforme invalide")
    return disconnect_cf_platform(user_id, platform)


# ---------------------------------------------------------------------------
# Stats (Sprint 4 — export monitoring)
# ---------------------------------------------------------------------------


@router.get("/stats/exports", response_model=CfExportStatsOut)
def cf_export_stats(user_id: str = Depends(_require_cf_user_id)) -> dict[str, Any]:
    return get_cf_export_stats(user_id)


# ---------------------------------------------------------------------------
# V1 Think — Ideas inbox
# ---------------------------------------------------------------------------


@router.get("/ideas", response_model=list[CfIdeaOut])
def list_cf_ideas_route(
    user_id: str = Depends(_require_cf_user_id),
    project_id: str | None = Query(default=None),
    status: str | None = Query(default=None),
) -> list[dict[str, Any]]:
    return list_cf_ideas(user_id, project_id=project_id, status=status)


@router.post("/ideas", response_model=CfIdeaOut, status_code=201)
def create_cf_idea_route(
    body: CfIdeaCreate,
    user_id: str = Depends(_require_cf_user_id),
) -> dict[str, Any]:
    return create_cf_idea(
        user_id,
        body.content,
        title=body.title,
        project_id=body.project_id,
        tags=body.tags,
        platform_target=body.platform_target,
        source_url=body.source_url,
        notes=body.notes,
    )


@router.get("/ideas/{idea_id}", response_model=CfIdeaOut)
def get_cf_idea_route(
    idea_id: str,
    user_id: str = Depends(_require_cf_user_id),
) -> dict[str, Any]:
    idea = get_cf_idea(idea_id, user_id)
    if not idea:
        raise HTTPException(status_code=404, detail="Idée introuvable")
    return idea


@router.patch("/ideas/{idea_id}", response_model=CfIdeaOut)
def update_cf_idea_route(
    idea_id: str,
    body: CfIdeaUpdate,
    user_id: str = Depends(_require_cf_user_id),
) -> dict[str, Any]:
    try:
        updated = update_cf_idea(idea_id, user_id, body.model_dump(exclude_unset=True))
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    if not updated:
        raise HTTPException(status_code=404, detail="Idée introuvable")
    return updated


@router.delete("/ideas/{idea_id}", status_code=204)
def delete_cf_idea_route(
    idea_id: str,
    user_id: str = Depends(_require_cf_user_id),
) -> None:
    if not delete_cf_idea(idea_id, user_id):
        raise HTTPException(status_code=404, detail="Idée introuvable")


@router.get("/ideas/{idea_id}/messages", response_model=list[CfIdeaMessageOut])
def list_idea_messages_route(
    idea_id: str,
    user_id: str = Depends(_require_cf_user_id),
) -> list[dict[str, Any]]:
    if not get_cf_idea(idea_id, user_id):
        raise HTTPException(status_code=404, detail="Idée introuvable")
    return list_idea_messages(idea_id, user_id)


@router.post("/ideas/{idea_id}/brainstorm", response_model=CfIdeaBrainstormResponse)
def brainstorm_idea_route(
    idea_id: str,
    body: CfIdeaBrainstormRequest,
    user_id: str = Depends(_require_cf_user_id),
) -> dict[str, Any]:
    if not get_cf_idea(idea_id, user_id):
        raise HTTPException(status_code=404, detail="Idée introuvable")
    try:
        return brainstorm_on_idea(idea_id, user_id, body.message)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/ideas/{idea_id}/artifacts", response_model=list[CfIdeaArtifactOut])
def list_idea_artifacts_route(
    idea_id: str,
    user_id: str = Depends(_require_cf_user_id),
    artifact_type: str | None = Query(default=None),
) -> list[dict[str, Any]]:
    if not get_cf_idea(idea_id, user_id):
        raise HTTPException(status_code=404, detail="Idée introuvable")
    return list_idea_artifacts(idea_id, user_id, artifact_type)


@router.post("/ideas/{idea_id}/generate-script", response_model=CfArtifactGenerateResponse)
def generate_script_route(
    idea_id: str,
    user_id: str = Depends(_require_cf_user_id),
) -> dict[str, Any]:
    try:
        return generate_script_for_idea(idea_id, user_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/ideas/{idea_id}/generate-shot-list", response_model=CfArtifactGenerateResponse)
def generate_shot_list_route(
    idea_id: str,
    user_id: str = Depends(_require_cf_user_id),
) -> dict[str, Any]:
    try:
        return generate_shot_list_for_idea(idea_id, user_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


# ---------------------------------------------------------------------------
# V1 Think — Creator DNA
# ---------------------------------------------------------------------------


@router.get("/dna", response_model=list[CfCreatorDnaOut])
def list_cf_dna_route(
    user_id: str = Depends(_require_cf_user_id),
    project_id: str | None = Query(default=None),
) -> list[dict[str, Any]]:
    return list_cf_creator_dna(user_id, project_id)


@router.put("/dna", response_model=CfCreatorDnaOut)
def upsert_cf_dna_route(
    body: CfCreatorDnaUpsert,
    user_id: str = Depends(_require_cf_user_id),
) -> dict[str, Any]:
    try:
        return upsert_cf_creator_dna(
            user_id,
            body.scope,
            project_id=body.project_id,
            voice_tone=body.voice_tone,
            audience=body.audience,
            brand_promise=body.brand_promise,
            taboos=body.taboos,
            style_refs=body.style_refs,
            extra=body.extra,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


# ---------------------------------------------------------------------------
# V1 Think — BYOK AI settings
# ---------------------------------------------------------------------------


@router.get("/ai-settings", response_model=CfUserAiSettingsOut)
def get_cf_ai_settings_route(user_id: str = Depends(_require_cf_user_id)) -> dict[str, Any]:
    return get_cf_ai_settings(user_id)


@router.put("/ai-settings", response_model=CfUserAiSettingsOut)
def upsert_cf_ai_settings_route(
    body: CfUserAiSettingsUpdate,
    user_id: str = Depends(_require_cf_user_id),
) -> dict[str, Any]:
    return upsert_cf_ai_settings(
        user_id,
        api_key=body.api_key,
        use_own_key=body.use_own_key,
        default_model=body.default_model,
    )


@router.delete("/ai-settings", status_code=204)
def delete_cf_ai_settings_route(user_id: str = Depends(_require_cf_user_id)) -> None:
    delete_cf_ai_settings(user_id)


# ---------------------------------------------------------------------------
# Studio — direct AI providers (Think → Studio → Publish)
# ---------------------------------------------------------------------------


@router.get("/studio/catalog", response_model=CfStudioCatalogOut)
def studio_catalog_route() -> dict[str, Any]:
    return get_studio_catalog()


@router.get("/studio/templates", response_model=list[CfStudioTemplateOut])
def studio_templates_route(
    platform: str | None = None,
    tool_id: str | None = None,
) -> list[dict[str, Any]]:
    return get_studio_templates(platform=platform, tool_id=tool_id)


@router.get("/ideas/{idea_id}/studio/prompt-preview", response_model=CfStudioPromptPreviewOut)
def studio_prompt_preview_route(
    idea_id: str,
    tool_id: str,
    shot_index: int | None = None,
    user_id: str = Depends(_require_cf_user_id),
) -> dict[str, Any]:
    idea = get_cf_idea(idea_id, user_id)
    if not idea:
        raise HTTPException(status_code=404, detail="Idée introuvable")
    try:
        preview = build_studio_prompt_preview(
            idea,
            user_id,
            tool_id=tool_id,
            shot_index=shot_index,
        )
        params = {k: v for k, v in (preview.get("default_params") or {}).items() if v is not None}
        preview["default_params"] = params
        return preview
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/ideas/{idea_id}/studio/jobs", response_model=list[CfStudioJobOut])
def list_studio_jobs_route(
    idea_id: str,
    user_id: str = Depends(_require_cf_user_id),
) -> list[dict[str, Any]]:
    return enrich_studio_jobs(list_studio_jobs_for_idea(idea_id, user_id))


@router.post("/ideas/{idea_id}/studio/jobs", response_model=CfStudioJobOut, status_code=201)
def create_studio_job_route(
    idea_id: str,
    body: CfStudioCreateJobRequest,
    background_tasks: BackgroundTasks,
    user_id: str = Depends(_require_cf_user_id),
) -> dict[str, Any]:
    try:
        job = create_studio_job(
            idea_id,
            user_id,
            tool_id=body.tool_id,
            prompt_override=body.prompt,
            params=body.params,
        )
        background_tasks.add_task(run_studio_job, job["id"], user_id)
        return job
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/studio/jobs/{job_id}", response_model=CfStudioJobOut)
def get_studio_job_route(
    job_id: str,
    user_id: str = Depends(_require_cf_user_id),
) -> dict[str, Any]:
    job = get_studio_job(job_id, user_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job Studio introuvable")
    return enrich_studio_job(job)


@router.post("/studio/jobs/{job_id}/run", response_model=CfStudioJobOut)
def run_studio_job_route(
    job_id: str,
    background_tasks: BackgroundTasks,
    user_id: str = Depends(_require_cf_user_id),
) -> dict[str, Any]:
    job = get_studio_job(job_id, user_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job Studio introuvable")
    if job.get("status") not in ("queued", "failed"):
        raise HTTPException(status_code=409, detail="Job non relançable")
    db = get_cf_supabase()
    db.update("cf_studio_jobs", job_id, {"status": "queued", "error_message": None})
    background_tasks.add_task(run_studio_job, job_id, user_id)
    return get_studio_job(job_id, user_id) or job


@router.post("/studio/jobs/{job_id}/link-asset")
def link_studio_job_asset_route(
    job_id: str,
    body: CfStudioLinkAssetRequest,
    user_id: str = Depends(_require_cf_user_id),
) -> dict[str, Any]:
    try:
        return link_studio_job_asset(
            job_id,
            user_id,
            file_url=body.file_url,
            title=body.title,
        )
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


# ---------------------------------------------------------------------------
# Studio Flows — node graphs (Bloc H)
# ---------------------------------------------------------------------------


def _flow_nodes_edges(body: CfStudioFlowCreateRequest | CfStudioFlowUpdateRequest) -> tuple:
    nodes = [n.model_dump() for n in body.nodes] if body.nodes is not None else None
    edges = [e.model_dump() for e in body.edges] if body.edges is not None else None
    return nodes, edges


@router.get("/ideas/{idea_id}/studio/flows", response_model=list[CfStudioFlowOut])
def list_studio_flows_route(
    idea_id: str,
    user_id: str = Depends(_require_cf_user_id),
) -> list[dict[str, Any]]:
    return list_studio_flows_for_idea(idea_id, user_id)


@router.post("/ideas/{idea_id}/studio/flows", response_model=CfStudioFlowOut, status_code=201)
def create_studio_flow_route(
    idea_id: str,
    body: CfStudioFlowCreateRequest,
    user_id: str = Depends(_require_cf_user_id),
) -> dict[str, Any]:
    nodes, edges = _flow_nodes_edges(body)
    try:
        return create_studio_flow(
            idea_id,
            user_id,
            name=body.name,
            nodes=nodes,
            edges=edges,
        )
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/studio/flows/{flow_id}", response_model=CfStudioFlowOut)
def get_studio_flow_route(
    flow_id: str,
    user_id: str = Depends(_require_cf_user_id),
) -> dict[str, Any]:
    flow = get_studio_flow(flow_id, user_id)
    if not flow:
        raise HTTPException(status_code=404, detail="Flow Studio introuvable")
    return flow


@router.put("/studio/flows/{flow_id}", response_model=CfStudioFlowOut)
def update_studio_flow_route(
    flow_id: str,
    body: CfStudioFlowUpdateRequest,
    user_id: str = Depends(_require_cf_user_id),
) -> dict[str, Any]:
    try:
        kwargs: dict[str, Any] = {}
        if body.name is not None:
            kwargs["name"] = body.name
        if body.nodes is not None:
            kwargs["nodes"] = [n.model_dump() for n in body.nodes]
        if body.edges is not None:
            kwargs["edges"] = [e.model_dump() for e in body.edges]
        return update_studio_flow(flow_id, user_id, **kwargs)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.delete("/studio/flows/{flow_id}", status_code=204)
def delete_studio_flow_route(
    flow_id: str,
    user_id: str = Depends(_require_cf_user_id),
) -> None:
    try:
        delete_studio_flow(flow_id, user_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/studio/flows/{flow_id}/run", response_model=CfStudioFlowRunOut)
def run_studio_flow_route(
    flow_id: str,
    background_tasks: BackgroundTasks,
    user_id: str = Depends(_require_cf_user_id),
) -> dict[str, Any]:
    flow = get_studio_flow(flow_id, user_id)
    if not flow:
        raise HTTPException(status_code=404, detail="Flow Studio introuvable")

    def _execute() -> None:
        try:
            run_studio_flow(flow_id, user_id)
        except Exception:
            pass

    background_tasks.add_task(_execute)
    return {
        "status": "running",
        "started_at": None,
        "node_jobs": {},
    }


# ---------------------------------------------------------------------------
# Pipeline — idea → asset → calendar
# ---------------------------------------------------------------------------


@router.get("/ideas/{idea_id}/pipeline", response_model=CfIdeaPipelineOut)
def idea_pipeline_route(
    idea_id: str,
    user_id: str = Depends(_require_cf_user_id),
) -> dict[str, Any]:
    try:
        return get_idea_pipeline(idea_id, user_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/ideas/{idea_id}/schedule", response_model=CfCalendarEntryOut)
def schedule_idea_route(
    idea_id: str,
    body: CfIdeaScheduleRequest,
    user_id: str = Depends(_require_cf_user_id),
) -> dict[str, Any]:
    try:
        result = schedule_idea_to_calendar(
            idea_id,
            user_id,
            platform=body.platform,
            scheduled_at=body.scheduled_at.isoformat() if body.scheduled_at else None,
            title=body.title,
            caption=body.caption,
        )
        return result["calendar_entry"]
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/ideas/{idea_id}/link-asset")
def link_asset_idea_route(
    idea_id: str,
    body: CfIdeaLinkAssetRequest,
    user_id: str = Depends(_require_cf_user_id),
) -> dict[str, Any]:
    try:
        return link_asset_to_idea(idea_id, user_id, body.asset_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
