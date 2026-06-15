"""CreatorFlow — real platform publish via Composio (Sprint 3)."""

from __future__ import annotations

import base64
import logging
from typing import Any

from skills.skill_composio import composio_execute
from services.creatorflow_platforms import cf_composio_user_id

logger = logging.getLogger(__name__)


def _composio_file(name: str, mime_type: str, content: bytes) -> dict[str, str]:
    """FileUploadable payload for Composio multipart / IG file actions."""
    return {
        "name": name,
        "mimetype": mime_type,
        "content": base64.b64encode(content).decode("ascii"),
    }


def _extract_id(data: Any, *keys: str) -> str | None:
    if not isinstance(data, dict):
        return None
    for key in keys:
        val = data.get(key)
        if val:
            return str(val)
    nested = data.get("data")
    if isinstance(nested, dict):
        for key in keys:
            val = nested.get(key)
            if val:
                return str(val)
    return None


def _build_caption(entry: dict[str, Any], adapted: dict[str, Any]) -> str:
    caption = adapted.get("adapted_caption") or entry.get("caption") or entry.get("title") or ""
    tags = adapted.get("adapted_hashtags") or entry.get("hashtags") or []
    if tags:
        tag_str = " ".join(f"#{t.lstrip('#')}" for t in tags if t)
        caption = f"{caption}\n\n{tag_str}".strip()
    return caption[:2200]


def publish_cf_youtube(
    user_id: str,
    entry: dict[str, Any],
    asset: dict[str, Any],
    adapted: dict[str, Any],
    video_bytes: bytes,
) -> dict[str, str]:
    """Upload video to YouTube via Composio multipart action."""
    composio_uid = cf_composio_user_id(user_id)
    filename = (asset.get("metadata") or {}).get("original_filename") or "video.mp4"
    mime = asset.get("mime_type") or "video/mp4"
    title = (adapted.get("adapted_title") or entry.get("title") or "CreatorFlow upload")[:100]
    description = _build_caption(entry, adapted)[:5000]
    tags = [str(t).lstrip("#") for t in (adapted.get("adapted_hashtags") or entry.get("hashtags") or [])][:10]

    result = composio_execute(
        "YOUTUBE_MULTIPART_UPLOAD_VIDEO",
        {
            "title": title,
            "description": description,
            "categoryId": "22",
            "privacyStatus": "private",
            "tags": tags or ["creatorflow"],
            "videoFile": _composio_file(filename, mime, video_bytes),
        },
        user_id=composio_uid,
    )
    if not result.get("success"):
        raise RuntimeError(result.get("error") or "YouTube upload failed")

    data = result.get("data")
    video_id = _extract_id(data, "id", "videoId", "video_id")
    if not video_id and isinstance(data, dict):
        video_id = _extract_id(data.get("snippet") or {}, "id")
    if not video_id:
        raise RuntimeError("YouTube upload succeeded but no video ID returned")

    return {
        "platform_post_id": video_id,
        "platform_post_url": f"https://www.youtube.com/watch?v={video_id}",
    }


def publish_cf_instagram(
    user_id: str,
    entry: dict[str, Any],
    asset: dict[str, Any],
    adapted: dict[str, Any],
    media_bytes: bytes,
) -> dict[str, str]:
    """Publish image or Reel to Instagram (container + publish)."""
    composio_uid = cf_composio_user_id(user_id)
    file_type = asset.get("file_type") or "video"
    filename = (asset.get("metadata") or {}).get("original_filename") or (
        "reel.mp4" if file_type == "video" else "post.jpg"
    )
    mime = asset.get("mime_type") or ("video/mp4" if file_type == "video" else "image/jpeg")
    caption = _build_caption(entry, adapted)
    file_payload = _composio_file(filename, mime, media_bytes)

    create_params: dict[str, Any] = {
        "ig_user_id": "me",
        "caption": caption,
    }
    if file_type == "video":
        create_params["video_file"] = file_payload
        create_params["media_type"] = "REELS"
    else:
        create_params["image_file"] = file_payload

    container = composio_execute(
        "INSTAGRAM_POST_IG_USER_MEDIA",
        create_params,
        user_id=composio_uid,
    )
    if not container.get("success"):
        raise RuntimeError(container.get("error") or "Instagram container creation failed")

    creation_id = _extract_id(container.get("data"), "id", "creation_id")
    if not creation_id:
        raise RuntimeError("Instagram container missing creation_id")

    publish = composio_execute(
        "INSTAGRAM_POST_IG_USER_MEDIA_PUBLISH",
        {
            "ig_user_id": "me",
            "creation_id": creation_id,
            "max_wait_seconds": 120,
        },
        user_id=composio_uid,
    )
    if not publish.get("success"):
        raise RuntimeError(publish.get("error") or "Instagram publish failed")

    media_id = _extract_id(publish.get("data"), "id", "media_id") or creation_id
    return {
        "platform_post_id": media_id,
        "platform_post_url": f"https://www.instagram.com/p/{media_id}/",
    }


def publish_cf_to_platform(
    platform: str,
    user_id: str,
    entry: dict[str, Any],
    asset: dict[str, Any],
    adapted: dict[str, Any],
    media_bytes: bytes,
) -> dict[str, str]:
    if platform == "youtube":
        if asset.get("file_type") != "video":
            raise RuntimeError("YouTube export requires a video asset")
        return publish_cf_youtube(user_id, entry, asset, adapted, media_bytes)
    if platform == "instagram":
        if asset.get("file_type") not in ("video", "image"):
            raise RuntimeError("Instagram export requires image or video")
        return publish_cf_instagram(user_id, entry, asset, adapted, media_bytes)
    raise RuntimeError(f"Unsupported platform: {platform}")
