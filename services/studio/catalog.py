"""Studio tool catalog — ALNUA-facing capabilities mapped to direct providers."""

from __future__ import annotations

from typing import Any

from config.settings import get_settings


# Post-prod uses local Pillow/rembg — no external API key.
_POSTPROD_TOOLS = frozenset({"upscale_image", "remove_bg", "resize_export"})


def _postprod_ready() -> bool:
    try:
        from PIL import Image  # noqa: F401

        return True
    except ImportError:
        return False


def _provider_has_key(provider: str) -> bool:
    import os

    if provider == "local":
        return _postprod_ready()
    cfg = get_settings()
    if provider == "google":
        return bool(cfg.studio_google_api_key.strip())
    if provider == "runway":
        key = cfg.studio_runway_api_key.strip() or os.getenv("RUNWAYML_API_SECRET", "").strip()
        return bool(key)
    if provider == "openrouter":
        return bool(cfg.openrouter_api_key.strip())
    if provider == "elevenlabs":
        return bool(cfg.studio_elevenlabs_api_key.strip())
    return False


def _tool_ready(provider: str, tool_id: str) -> bool:
    if tool_id in _POSTPROD_TOOLS:
        return _postprod_ready()
    return _provider_has_key(provider)


# Static catalog — providers wired in services/studio/providers/ incrementally.
STUDIO_TOOLS: list[dict[str, Any]] = [
    {
        "id": "veo3_video",
        "label": "Vidéo 16:9",
        "description": "YouTube, paysage, master horizontal",
        "capability": "video_generate",
        "provider": "google",
        "model_slug": "veo-3.1-generate-preview",
        "default_aspect": "16:9",
        "platforms": ["youtube", "instagram", "both"],
    },
    {
        "id": "veo3_shorts",
        "label": "Reel / Shorts 9:16",
        "description": "Vertical TikTok, Reels, Shorts",
        "capability": "video_generate",
        "provider": "google",
        "model_slug": "veo-3.1-generate-preview",
        "default_aspect": "9:16",
        "platforms": ["instagram", "both"],
    },
    {
        "id": "imagen_image",
        "label": "Image carré / feed",
        "description": "Visuel feed 1:1 ou 4:5",
        "capability": "image_generate",
        "provider": "google",
        "model_slug": "imagen-3.0-generate-002",
        "default_aspect": "1:1",
        "platforms": ["youtube", "instagram", "both"],
    },
    {
        "id": "thumbnail_image",
        "label": "Miniature YouTube",
        "description": "Thumbnail 16:9 accrocheur",
        "capability": "image_generate",
        "provider": "google",
        "model_slug": "imagen-3.0-generate-002",
        "default_aspect": "16:9",
        "platforms": ["youtube", "both"],
    },
    {
        "id": "runway_video",
        "label": "Runway Gen-4",
        "description": "Text-to-video, mouvement cinéma",
        "capability": "video_generate",
        "provider": "runway",
        "model_slug": "gen4_turbo",
        "default_aspect": "16:9",
        "platforms": ["youtube", "instagram", "both"],
    },
    {
        "id": "runway_i2v",
        "label": "Runway image → vidéo",
        "description": "Animer une image de référence",
        "capability": "video_generate",
        "provider": "runway",
        "model_slug": "gen4_turbo",
        "default_aspect": "16:9",
        "platforms": ["youtube", "instagram", "both"],
    },
    {
        "id": "flux_image",
        "label": "Flux Pro",
        "description": "Image stylisée haute qualité",
        "capability": "image_generate",
        "provider": "openrouter",
        "model_slug": "black-forest-labs/flux-1.1-pro",
        "default_aspect": "1:1",
        "platforms": ["youtube", "instagram", "both"],
    },
    {
        "id": "upscale_image",
        "label": "Upscale 2×",
        "description": "Améliorer résolution d'un visuel",
        "capability": "image_enhance",
        "provider": "local",
        "model_slug": "pillow-lanczos",
        "default_aspect": "n/a",
        "platforms": ["youtube", "instagram", "both"],
    },
    {
        "id": "remove_bg",
        "label": "Détourage",
        "description": "Fond transparent pour produit / logo",
        "capability": "image_edit",
        "provider": "local",
        "model_slug": "rembg",
        "default_aspect": "n/a",
        "platforms": ["youtube", "instagram", "both"],
    },
    {
        "id": "resize_export",
        "label": "Export multi-format",
        "description": "16:9 · 9:16 · 4:5 depuis un master",
        "capability": "export_format",
        "provider": "local",
        "model_slug": "pillow-export",
        "default_aspect": "n/a",
        "platforms": ["youtube", "instagram", "both"],
    },
    {
        "id": "google_tts",
        "label": "Voix off",
        "description": "Narration IA (Google Gemini TTS)",
        "capability": "tts",
        "provider": "google",
        "model_slug": "gemini-2.5-flash-preview-tts",
        "default_aspect": "n/a",
        "platforms": ["youtube", "instagram", "both"],
    },
    {
        "id": "elevenlabs_tts",
        "label": "Voix off premium",
        "description": "Narration naturelle (ElevenLabs)",
        "capability": "tts",
        "provider": "elevenlabs",
        "model_slug": "eleven_multilingual_v2",
        "default_aspect": "n/a",
        "platforms": ["youtube", "instagram", "both"],
    },
]


def get_studio_catalog() -> dict[str, Any]:
    tools = []
    for tool in STUDIO_TOOLS:
        provider = tool["provider"]
        tools.append(
            {
                **tool,
                "provider_ready": _tool_ready(provider, tool["id"]),
            }
        )
    return {
        "tools": tools,
        "providers": {
            "google": {"ready": _provider_has_key("google"), "label": "Google AI"},
            "runway": {"ready": _provider_has_key("runway"), "label": "Runway"},
            "openrouter": {"ready": _provider_has_key("openrouter"), "label": "OpenRouter"},
            "elevenlabs": {"ready": _provider_has_key("elevenlabs"), "label": "ElevenLabs"},
            "local": {"ready": _postprod_ready(), "label": "Post-prod ALNUA"},
        },
    }
