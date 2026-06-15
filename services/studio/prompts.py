"""Build production prompts from Think context (idea + DNA)."""

from __future__ import annotations

from typing import Any

from database.creatorflow_supabase_client import get_cf_supabase
from database.supabase_client import SupabaseClient
from services.creatorflow_brainstorm import list_idea_artifacts
from services.creatorflow_dna import build_dna_context_block

ASPECT_BY_PLATFORM = {
    "youtube": "16:9 — vidéo longue ou Shorts 9:16",
    "instagram": "9:16 Reels ou 4:5 feed",
    "both": "variants 16:9 + 9:16",
}

_MAX_TTS_CHARS = 8000


def build_studio_prompt(idea: dict[str, Any], user_id: str) -> str:
    dna = build_dna_context_block(user_id, idea.get("project_id"))
    platform = idea.get("platform_target") or "both"
    aspect = ASPECT_BY_PLATFORM.get(platform, ASPECT_BY_PLATFORM["both"])
    return (
        f"CreatorFlow Studio — production brief\n\n"
        f"Titre: {idea.get('title')}\n"
        f"Concept: {idea.get('content')}\n"
        f"Plateforme: {platform} ({aspect})\n\n"
        f"{dna}\n\n"
        "Objectif: contenu visuel cohérent avec la marque. "
        "Hook fort dans les 2 premières secondes."
    )


def _script_text_from_artifact(content: dict[str, Any]) -> str:
    parts: list[str] = []
    hook = content.get("hook")
    if hook:
        parts.append(str(hook).strip())
    for sec in content.get("sections") or []:
        if isinstance(sec, dict) and sec.get("script"):
            parts.append(str(sec["script"]).strip())
    title = content.get("title")
    if title and not parts:
        parts.append(str(title).strip())
    return "\n\n".join(p for p in parts if p)


def _shot_at_index(
    idea_id: str,
    user_id: str,
    shot_index: int | None,
    db: SupabaseClient,
) -> dict[str, Any] | None:
    if shot_index is None or shot_index < 0:
        return None
    shot_lists = list_idea_artifacts(idea_id, user_id, "shot_list", db)
    if not shot_lists:
        return None
    shots = (shot_lists[0].get("content") or {}).get("shots") or []
    if shot_index >= len(shots) or not isinstance(shots[shot_index], dict):
        return None
    return shots[shot_index]


def _shot_prompt_block(shot: dict[str, Any], shot_index: int) -> str:
    number = shot.get("number") or shot_index + 1
    lines = [
        f"Plan de tournage — Plan {number}",
        f"Type: {shot.get('type') or 'plan'}",
        f"Scène: {shot.get('description') or ''}",
    ]
    if shot.get("setup"):
        lines.append(f"Setup: {shot['setup']}")
    if shot.get("notes"):
        lines.append(f"Notes: {shot['notes']}")
    if shot.get("duration_sec") is not None:
        lines.append(f"Durée cible: {shot['duration_sec']}s")
    lines.append("")
    lines.append("Focus visuel exclusif sur ce plan.")
    return "\n".join(lines)


def _video_duration_from_shot(shot: dict[str, Any] | None, default: int = 5) -> int:
    if not shot:
        return default
    try:
        sec = int(shot.get("duration_sec") or default)
    except (TypeError, ValueError):
        return default
    if sec >= 8:
        return 10
    if sec >= 5:
        return 5
    return 3


def build_tts_prompt(
    idea: dict[str, Any],
    user_id: str,
    db: SupabaseClient | None = None,
) -> str:
    """Narration-ready text — prefers generated script over raw idea content."""
    idea_id = str(idea.get("id") or "")
    scripts = list_idea_artifacts(idea_id, user_id, "script", db) if idea_id else []
    if scripts:
        body = _script_text_from_artifact(scripts[0].get("content") or {})
        narration = body or str(idea.get("content") or idea.get("title") or "").strip()
    else:
        narration = str(idea.get("content") or idea.get("title") or "").strip()

    if not narration:
        raise ValueError("Aucun texte à narrer — ajoutez un script ou du contenu à l'idée")

    dna = build_dna_context_block(user_id, idea.get("project_id"))
    tone_hint = f"\n\nTon de voix (Creator DNA):\n{dna[:1500]}" if dna else ""

    return f"{narration}{tone_hint}".strip()[:_MAX_TTS_CHARS]


def build_studio_prompt_preview(
    idea: dict[str, Any],
    user_id: str,
    *,
    tool_id: str,
    shot_index: int | None = None,
    db: SupabaseClient | None = None,
) -> dict[str, Any]:
    """Client-facing prompt draft before job creation."""
    db = db or get_cf_supabase()
    idea_id = str(idea.get("id") or "")
    shot = _shot_at_index(idea_id, user_id, shot_index, db) if idea_id else None

    is_tts = "tts" in tool_id
    is_postprod = tool_id in ("upscale_image", "remove_bg", "resize_export")
    if is_tts:
        prompt = build_tts_prompt(idea, user_id, db)
        return {
            "prompt_kind": "narration",
            "prompt": prompt,
            "negative_prompt": "",
            "style_tags": [],
            "default_params": {},
        }

    if is_postprod:
        labels = {
            "upscale_image": "Upscale 2× — amélioration résolution",
            "remove_bg": "Détourage — fond transparent",
            "resize_export": "Export multi-format — recadrage plateforme",
        }
        aspect = "16:9"
        if tool_id == "resize_export":
            platform = idea.get("platform_target") or "both"
            aspect = "9:16" if platform == "instagram" else "16:9"
        return {
            "prompt_kind": "visual",
            "prompt": labels.get(tool_id, "Post-prod ALNUA"),
            "negative_prompt": "",
            "style_tags": [],
            "default_params": {"aspect_ratio": aspect} if tool_id == "resize_export" else {},
        }

    visual = build_studio_prompt(idea, user_id)
    scripts = list_idea_artifacts(idea_id, user_id, "script", db) if idea_id else []
    if scripts:
        script_body = _script_text_from_artifact(scripts[0].get("content") or {})
        if script_body:
            visual = f"{visual}\n\nScène / narration:\n{script_body[:2000]}"

    if shot:
        visual = f"{visual}\n\n{_shot_prompt_block(shot, shot_index or 0)}"

    platform = idea.get("platform_target") or "both"
    aspect = "9:16" if "shorts" in tool_id or platform == "instagram" else "16:9"
    if "thumbnail" in tool_id:
        aspect = "16:9"
    if "image" in tool_id and "thumbnail" not in tool_id and "flux" not in tool_id:
        aspect = "1:1" if platform != "instagram" else "4:5"

    is_video = "video" in tool_id or "veo" in tool_id or "runway" in tool_id
    duration = _video_duration_from_shot(shot, 5) if is_video else None

    return {
        "prompt_kind": "visual",
        "prompt": visual,
        "negative_prompt": "flou, basse qualité, watermark, texte illisible, distorsions",
        "style_tags": ["cinématique", "UGC authentique", "minimal", "énergique"],
        "default_params": {
            "aspect_ratio": aspect,
            "duration": duration,
        },
    }
