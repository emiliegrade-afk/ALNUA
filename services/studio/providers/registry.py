"""Dispatch Studio jobs to the correct provider adapter."""

from __future__ import annotations

from typing import Any, Callable

from database.creatorflow_supabase_client import get_cf_supabase
from services.studio.providers.elevenlabs_tts import generate_elevenlabs_tts
from services.studio.providers.google_imagen import generate_imagen_image
from services.studio.providers.google_tts import generate_google_tts
from services.studio.providers.google_veo import generate_veo_video
from services.studio.providers.openrouter_image import generate_openrouter_image
from services.studio.providers.remove_bg import remove_background_bytes
from services.studio.providers.resize_export import resize_export_bytes
from services.studio.providers.runway_video import generate_runway_video
from services.studio.providers.upscale import upscale_image_bytes

# tool_id → executor(prompt, params, model_slug) → (bytes, mime_type, filename)
Executor = Callable[[str, dict[str, Any], str], tuple[bytes, str, str]]

_EXECUTORS: dict[str, Executor] = {
    "veo3_video": lambda prompt, params, slug: _veo(prompt, params, slug),
    "veo3_shorts": lambda prompt, params, slug: _veo(prompt, params, slug),
    "imagen_image": lambda prompt, params, slug: _imagen(prompt, params, slug),
    "thumbnail_image": lambda prompt, params, slug: _imagen(prompt, params, slug),
    "runway_video": lambda prompt, params, slug: _runway(prompt, params, slug),
    "runway_i2v": lambda prompt, params, slug: _runway(prompt, params, slug),
    "flux_image": lambda prompt, params, slug: _flux(prompt, params, slug),
    "google_tts": lambda prompt, params, slug: _google_tts(prompt, params, slug),
    "elevenlabs_tts": lambda prompt, params, slug: _elevenlabs_tts(prompt, params, slug),
    "upscale_image": lambda prompt, params, slug: _upscale(prompt, params, slug),
    "remove_bg": lambda prompt, params, slug: _remove_bg(prompt, params, slug),
    "resize_export": lambda prompt, params, slug: _resize_export(prompt, params, slug),
}


def _aspect(params: dict[str, Any], default: str = "16:9") -> str:
    return str(params.get("aspect_ratio") or params.get("aspectRatio") or default)


def _veo(prompt: str, params: dict[str, Any], slug: str) -> tuple[bytes, str, str]:
    content = generate_veo_video(prompt, aspect_ratio=_aspect(params, "16:9"), model=slug)
    return content, "video/mp4", "studio-veo.mp4"


def _imagen(prompt: str, params: dict[str, Any], slug: str) -> tuple[bytes, str, str]:
    content = generate_imagen_image(prompt, aspect_ratio=_aspect(params, "1:1"), model=slug)
    return content, "image/png", "studio-imagen.png"


def _duration(params: dict[str, Any], default: int = 5) -> int:
    raw = params.get("duration") or params.get("duration_seconds")
    try:
        return int(raw)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return default


def _runway(prompt: str, params: dict[str, Any], slug: str) -> tuple[bytes, str, str]:
    prompt_image = params.get("prompt_image") or params.get("promptImage")
    image_uri = str(prompt_image).strip() if prompt_image else None
    content = generate_runway_video(
        prompt,
        model=slug,
        aspect_ratio=_aspect(params, "16:9"),
        duration=_duration(params, 5),
        prompt_image=image_uri or None,
    )
    return content, "video/mp4", "studio-runway.mp4"


def _google_tts(prompt: str, params: dict[str, Any], slug: str) -> tuple[bytes, str, str]:
    voice = str(params.get("voice_name") or params.get("voice") or "Kore")
    content, mime = generate_google_tts(prompt, model=slug, voice_name=voice)
    ext = "mp3" if mime == "audio/mpeg" else "wav"
    return content, mime, f"studio-google-tts.{ext}"


def _elevenlabs_tts(prompt: str, params: dict[str, Any], slug: str) -> tuple[bytes, str, str]:
    voice_id = params.get("voice_id")
    content, mime = generate_elevenlabs_tts(
        prompt,
        model=slug,
        voice_id=str(voice_id) if voice_id else None,
    )
    return content, mime, "studio-elevenlabs.mp3"


def _flux(prompt: str, params: dict[str, Any], slug: str) -> tuple[bytes, str, str]:
    model = str(params.get("model") or slug)
    content = generate_openrouter_image(prompt, model=model)
    return content, "image/png", "studio-image.png"


def _studio_user_id(params: dict[str, Any]) -> str:
    return str(params.get("_studio_user_id") or "")


def _upscale(prompt: str, params: dict[str, Any], slug: str) -> tuple[bytes, str, str]:
    db = get_cf_supabase()
    content = upscale_image_bytes(params, _studio_user_id(params), db)
    return content, "image/png", "studio-upscale.png"


def _remove_bg(prompt: str, params: dict[str, Any], slug: str) -> tuple[bytes, str, str]:
    db = get_cf_supabase()
    content = remove_background_bytes(params, _studio_user_id(params), db)
    return content, "image/png", "studio-nobg.png"


def _resize_export(prompt: str, params: dict[str, Any], slug: str) -> tuple[bytes, str, str]:
    db = get_cf_supabase()
    content = resize_export_bytes(params, _studio_user_id(params), db)
    aspect = str(params.get("aspect_ratio") or "16x9").replace(":", "x")
    return content, "image/png", f"studio-export-{aspect}.png"


def execute_studio_tool(
    tool_id: str,
    prompt: str,
    params: dict[str, Any],
    model_slug: str,
) -> tuple[bytes, str, str]:
    fn = _EXECUTORS.get(tool_id)
    if not fn:
        raise ValueError(f"Aucun provider Studio pour l'outil {tool_id}")
    return fn(prompt, params or {}, model_slug)
