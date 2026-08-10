"""Hook Content Studio posts → content_validation workflow (Phase 30)."""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)

# Posts queue statuses that mean "ready for validation pipeline".
_READY_STATUSES = frozenset({"pending_approval", "approved"})


def post_to_artifact(post: dict[str, Any]) -> dict[str, Any]:
    """Map posts_queue row to workflow validation artifact."""
    text = str(post.get("text_content") or post.get("content") or "").strip()
    title = text.split("\n", 1)[0][:120] if text else str(post.get("title") or "Post")
    return {
        "title": title,
        "body": text,
        "status": "ready",
        "platform": post.get("platform") or post.get("channel") or "",
        "project_id": post.get("project_id"),
        "campaign_id": post.get("campaign_id"),
        "producer_agent_id": post.get("author_agent_id") or post.get("author_agent") or "",
        "post_id": post.get("id"),
    }


def trigger_on_post_status(
    post: dict[str, Any],
    *,
    previous_status: str | None = None,
) -> dict[str, Any] | None:
    """Run content_validation when a post newly reaches a ready status."""
    new_status = str(post.get("status") or "").strip().lower()
    if new_status not in _READY_STATUSES:
        return None
    prev = str(previous_status or "").strip().lower()
    if prev == new_status:
        return None

    producer = str(
        post.get("author_agent_id") or post.get("author_agent") or "content"
    ).strip()
    from services.autonomy_resolver import resolve_autonomy_level
    from services.workflow_engine import run_workflow

    artifact = post_to_artifact(post)
    autonomy = resolve_autonomy_level(producer)
    context: dict[str, Any] = {
        "autonomy_level": autonomy,
        "producer_agent_id": producer,
        "project_id": post.get("project_id"),
        "campaign_id": post.get("campaign_id"),
        "artifact": artifact,
        "source": "posts_queue",
        "post_id": post.get("id"),
    }

    try:
        result = run_workflow("content_validation", context)
        logger.info(
            "content_validation for post %s status=%s run=%s success=%s",
            post.get("id"),
            new_status,
            result.get("run_id"),
            result.get("success"),
        )
        return result
    except Exception as exc:
        logger.exception("content_validation trigger failed for post %s", post.get("id"))
        return {"success": False, "error": str(exc)[:200]}
