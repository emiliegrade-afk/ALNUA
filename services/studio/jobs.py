"""Studio async jobs — persisted in cf_studio_jobs."""

from __future__ import annotations

from typing import Any

from database.creatorflow_supabase_client import get_cf_supabase
from database.supabase_client import SupabaseClient
from services.creatorflow_ideas import get_cf_idea, update_cf_idea
from services.studio.catalog import STUDIO_TOOLS
from services.creatorflow_storage import sign_storage_path
from services.studio.prompts import build_studio_prompt, build_tts_prompt

_CF_JOBS = "cf_studio_jobs"


def enrich_studio_job(
    job: dict[str, Any],
    db: SupabaseClient | None = None,
) -> dict[str, Any]:
    """Sign storage paths in artifact_url for client preview."""
    out = dict(job)
    url = out.get("artifact_url") or ""
    if url and not url.startswith("http"):
        db = db or get_cf_supabase()
        out["artifact_url"] = sign_storage_path(db, url)
    return out


def enrich_studio_jobs(
    jobs: list[dict[str, Any]],
    db: SupabaseClient | None = None,
) -> list[dict[str, Any]]:
    db = db or get_cf_supabase()
    return [enrich_studio_job(j, db) for j in jobs]


def _tool_by_id(tool_id: str) -> dict[str, Any] | None:
    return next((t for t in STUDIO_TOOLS if t["id"] == tool_id), None)


def create_studio_job(
    idea_id: str,
    user_id: str,
    *,
    tool_id: str,
    prompt_override: str | None = None,
    params: dict[str, Any] | None = None,
    db: SupabaseClient | None = None,
) -> dict[str, Any]:
    db = db or get_cf_supabase()
    idea = get_cf_idea(idea_id, user_id, db)
    if not idea:
        raise ValueError("Idée introuvable")

    tool = _tool_by_id(tool_id)
    if not tool:
        raise ValueError(f"Outil Studio inconnu: {tool_id}")

    if tool["capability"] == "tts":
        prompt = (prompt_override or "").strip() or build_tts_prompt(idea, user_id, db)
    else:
        prompt = (prompt_override or "").strip() or build_studio_prompt(idea, user_id)
    merged_params = dict(params or {})
    default_aspect = tool.get("default_aspect")
    if default_aspect and default_aspect != "n/a":
        if "aspect_ratio" not in merged_params and "aspectRatio" not in merged_params:
            merged_params["aspect_ratio"] = default_aspect
    return db.insert(
        _CF_JOBS,
        {
            "idea_id": idea_id,
            "user_id": user_id,
            "project_id": idea.get("project_id"),
            "tool_id": tool_id,
            "capability": tool["capability"],
            "provider": tool["provider"],
            "model_slug": tool["model_slug"],
            "status": "queued",
            "prompt": prompt,
            "params": merged_params,
            "error_message": None,
            "artifact_url": None,
            "asset_id": None,
        },
    )


def list_studio_jobs_for_idea(
    idea_id: str,
    user_id: str,
    db: SupabaseClient | None = None,
) -> list[dict[str, Any]]:
    db = db or get_cf_supabase()
    if not get_cf_idea(idea_id, user_id, db):
        return []
    return db.select(
        _CF_JOBS,
        filters={"idea_id": idea_id, "user_id": user_id},
        order_by="created_at",
        ascending=False,
    )


def get_studio_job(
    job_id: str,
    user_id: str,
    db: SupabaseClient | None = None,
) -> dict[str, Any] | None:
    db = db or get_cf_supabase()
    rows = db.select(_CF_JOBS, filters={"id": job_id, "user_id": user_id}, limit=1)
    return rows[0] if rows else None


def link_studio_job_asset(
    job_id: str,
    user_id: str,
    *,
    file_url: str,
    title: str | None = None,
    db: SupabaseClient | None = None,
) -> dict[str, Any]:
    """Attach a completed artifact URL to a job and link asset to the idea."""
    db = db or get_cf_supabase()
    job = get_studio_job(job_id, user_id, db)
    if not job:
        raise ValueError("Job Studio introuvable")

    idea_id = job["idea_id"]
    idea = get_cf_idea(idea_id, user_id, db)
    if not idea:
        raise ValueError("Idée introuvable")

    url = file_url.strip()
    file_type = "video" if any(x in url.lower() for x in (".mp4", ".mov", ".webm")) else "image"
    asset_title = title or f"Studio — {idea.get('title', 'asset')}"[:500]

    asset = db.insert(
        "cf_assets",
        {
            "user_id": user_id,
            "project_id": idea.get("project_id"),
            "title": asset_title,
            "file_url": url,
            "file_type": file_type,
            "status": "pending",
            "metadata": {
                "source": "studio",
                "idea_id": idea_id,
                "job_id": job_id,
                "tool_id": job.get("tool_id"),
                "provider": job.get("provider"),
            },
        },
    )

    db.update(
        _CF_JOBS,
        job_id,
        {
            "status": "succeeded",
            "artifact_url": url,
            "asset_id": asset["id"],
        },
    )

    update_cf_idea(
        idea_id,
        user_id,
        {"status": "in_production", "linked_asset_id": asset["id"]},
        db,
    )
    return {"job_id": job_id, "asset": asset, "idea_id": idea_id}
