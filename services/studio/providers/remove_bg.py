"""Background removal via rembg."""

from __future__ import annotations

from io import BytesIO
from typing import Any

from PIL import Image
from rembg import remove

from database.supabase_client import SupabaseClient
from services.studio.providers.source_image import (
    image_to_png_bytes,
    load_image_from_params,
)


def remove_background_bytes(
    params: dict[str, Any],
    user_id: str,
    db: SupabaseClient,
) -> bytes:
    image = load_image_from_params(params, user_id, db)
    rgba = image.convert("RGBA")
    result = remove(rgba)
    if isinstance(result, bytes):
        out = Image.open(BytesIO(result)).convert("RGBA")
    else:
        out = result.convert("RGBA")
    return image_to_png_bytes(out)
