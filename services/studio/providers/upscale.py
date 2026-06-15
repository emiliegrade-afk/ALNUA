"""2× image upscale via Pillow LANCZOS."""

from __future__ import annotations

from typing import Any

from PIL import Image

from database.supabase_client import SupabaseClient
from services.studio.providers.source_image import (
    image_to_png_bytes,
    load_image_from_params,
)


def upscale_image_bytes(
    params: dict[str, Any],
    user_id: str,
    db: SupabaseClient,
) -> bytes:
    scale = _scale_factor(params)
    image = load_image_from_params(params, user_id, db)
    w, h = image.size
    upscaled = image.resize((w * scale, h * scale), Image.Resampling.LANCZOS)
    return image_to_png_bytes(upscaled)


def _scale_factor(params: dict[str, Any]) -> int:
    raw = params.get("scale") or params.get("upscale_factor") or 2
    try:
        value = int(raw)
    except (TypeError, ValueError):
        value = 2
    return max(2, min(value, 4))
