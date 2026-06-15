"""Execute queued Studio jobs — provider call → storage → asset link."""

from __future__ import annotations

import logging
from typing import Any

from database.creatorflow_supabase_client import get_cf_supabase
from database.supabase_client import SupabaseClient
from services.creatorflow_ideas import update_cf_idea
from services.creatorflow_storage import upload_cf_asset_file
from services.studio.jobs import get_studio_job
from services.studio.providers.registry import execute_studio_tool
from services.studio.references import resolve_studio_job_params

logger = logging.getLogger(__name__)

_CF_JOBS = "cf_studio_jobs"
_CF_ASSETS = "cf_assets"


def run_studio_job(job_id: str, user_id: str, db: SupabaseClient | None = None) -> None:
    """Background task: queued → running → succeeded|failed."""
    db = db or get_cf_supabase()
    job = get_studio_job(job_id, user_id, db)
    if not job:
        logger.warning("Studio job %s introuvable", job_id)
        return
    if job.get("status") not in ("queued", "running"):
        return

    db.update(_CF_JOBS, job_id, {"status": "running", "error_message": None})

    try:
        resolved_params = resolve_studio_job_params(job.get("params") or {}, user_id, db)
        resolved_params["_studio_user_id"] = user_id
        content, mime_type, filename = execute_studio_tool(
            job["tool_id"],
            job["prompt"],
            resolved_params,
            job.get("model_slug") or "",
        )
        result = _persist_artifact(db, job, user_id, content, mime_type, filename)
        db.update(
            _CF_JOBS,
            job_id,
            {
                "status": "succeeded",
                "artifact_url": result["file_url"],
                "asset_id": result["asset_id"],
                "error_message": None,
            },
        )
        update_cf_idea(
            job["idea_id"],
            user_id,
            {"status": "in_production", "linked_asset_id": result["asset_id"]},
            db,
        )
        logger.info("Studio job %s succeeded → asset %s", job_id, result["asset_id"])
    except Exception as exc:
        logger.exception("Studio job %s failed", job_id)
        db.update(
            _CF_JOBS,
            job_id,
            {"status": "failed", "error_message": str(exc)[:500]},
        )


def _persist_artifact(
    db: SupabaseClient,
    job: dict[str, Any],
    user_id: str,
    content: bytes,
    mime_type: str,
    filename: str,
) -> dict[str, str]:
    storage_path = upload_cf_asset_file(db, user_id, content, filename, mime_type)
    if mime_type.startswith("video/"):
        file_type = "video"
    elif mime_type.startswith("audio/"):
        file_type = "audio"
    elif mime_type.startswith("image/"):
        file_type = "image"
    else:
        file_type = "text"
    idea_id = job["idea_id"]

    asset = db.insert(
        _CF_ASSETS,
        {
            "user_id": user_id,
            "project_id": job.get("project_id"),
            "title": f"Studio — {job.get('tool_id', 'asset')}"[:500],
            "file_url": storage_path,
            "file_type": file_type,
            "mime_type": mime_type,
            "file_size_bytes": len(content),
            "status": "pending",
            "metadata": {
                "source": "studio",
                "idea_id": idea_id,
                "job_id": job["id"],
                "tool_id": job.get("tool_id"),
                "provider": job.get("provider"),
            },
        },
    )
    return {"asset_id": asset["id"], "file_url": storage_path}
