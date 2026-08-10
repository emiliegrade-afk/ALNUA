"""Brand segmentation — rembg, canvas fit, and element lookup."""
from __future__ import annotations

import io
from pathlib import Path

import numpy as np
from PIL import Image
from rembg import remove

from services.brand_schemas import BrandAnalysis, BrandElement


def apply_rembg(image: Image.Image) -> Image.Image:
    buffer = io.BytesIO()
    image.convert("RGBA").save(buffer, format="PNG")
    result_bytes = remove(buffer.getvalue())
    return Image.open(io.BytesIO(result_bytes)).convert("RGBA")


def tighten_transparent_crop(image: Image.Image) -> Image.Image:
    """After rembg, trim empty alpha — does not alter LLM bbox, only isolated output."""
    rgba = image.convert("RGBA")
    alpha = np.array(rgba.split()[3])
    ys, xs = np.where(alpha > 16)
    if len(xs) == 0 or len(ys) == 0:
        return rgba
    pad = max(2, int(min(rgba.size) * 0.02))
    left = max(0, int(xs.min()) - pad)
    top = max(0, int(ys.min()) - pad)
    right = min(rgba.width, int(xs.max()) + pad + 1)
    bottom = min(rgba.height, int(ys.max()) + pad + 1)
    return rgba.crop((left, top, right, bottom))


def fit_on_canvas(
    image: Image.Image,
    canvas_size: tuple[int, int],
    *,
    background: tuple[int, int, int, int] | None = None,
) -> Image.Image:
    """Scale image to fit inside canvas, centered."""
    target_w, target_h = canvas_size
    if background is None:
        canvas = Image.new("RGBA", canvas_size, (0, 0, 0, 0))
    else:
        canvas = Image.new("RGBA", canvas_size, background)

    src = image.convert("RGBA")
    src_w, src_h = src.size
    if src_w == 0 or src_h == 0:
        return canvas

    scale = min(target_w / src_w, target_h / src_h)
    new_w = max(1, int(src_w * scale))
    new_h = max(1, int(src_h * scale))
    resized = src.resize((new_w, new_h), Image.Resampling.LANCZOS)

    offset_x = (target_w - new_w) // 2
    offset_y = (target_h - new_h) // 2
    canvas.paste(resized, (offset_x, offset_y), resized)
    return canvas


def relative_path(file_path: Path) -> str:
    repo_root = Path(__file__).resolve().parent.parent
    return str(file_path.relative_to(repo_root)).replace("\\", "/")


def find_element(
    elements: list[BrandElement],
    *,
    labels: tuple[str, ...],
    element_type: str | None = None,
) -> BrandElement | None:
    lowered_labels = [label.lower() for label in labels]
    for element in elements:
        element_label = element.label.lower()
        if element_label in lowered_labels:
            return element
        if any(label in element_label for label in lowered_labels):
            return element
    if element_type:
        for element in elements:
            if element.type == element_type:
                return element
    return None


def primary_bg_color(brand_data: BrandAnalysis) -> str:
    for color in brand_data.colors:
        if color.role == "primary_bg":
            return color.hex
    if brand_data.colors:
        return brand_data.colors[0].hex
    return "#1A1A1A"
