"""Export image to platform aspect ratios (cover crop + resize)."""

from __future__ import annotations

from typing import Any

from PIL import Image

from database.supabase_client import SupabaseClient
from services.studio.providers.source_image import (
    image_to_png_bytes,
    load_image_from_params,
)

_ASPECT_PIXELS: dict[str, tuple[int, int]] = {
    "16:9": (1920, 1080),
    "9:16": (1080, 1920),
    "4:5": (1080, 1350),
    "1:1": (1080, 1080),
}


def resize_export_bytes(
    params: dict[str, Any],
    user_id: str,
    db: SupabaseClient,
) -> bytes:
    aspect = str(params.get("aspect_ratio") or params.get("aspectRatio") or "16:9")
    target_w, target_h = _ASPECT_PIXELS.get(aspect, _ASPECT_PIXELS["16:9"])
    image = load_image_from_params(params, user_id, db)
    fitted = _fit_cover(image, target_w, target_h)
    return image_to_png_bytes(fitted)


def _fit_cover(image: Image.Image, target_w: int, target_h: int) -> Image.Image:
    src_w, src_h = image.size
    if src_w <= 0 or src_h <= 0:
        raise ValueError("Image source invalide")
    scale = max(target_w / src_w, target_h / src_h)
    new_w = max(1, int(src_w * scale))
    new_h = max(1, int(src_h * scale))
    resized = image.resize((new_w, new_h), Image.Resampling.LANCZOS)
    left = max(0, (new_w - target_w) // 2)
    top = max(0, (new_h - target_h) // 2)
    return resized.crop((left, top, left + target_w, top + target_h))
