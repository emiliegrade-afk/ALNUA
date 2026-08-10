"""Brand kit render — shared Pillow helpers."""

from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageFont

from services.brand_schemas import BrandAnalysis
from services.kit_generator_specs import PADDING_RATIO
from services.segmentation import (
    _apply_rembg,
    _crop_element,
    _find_element,
    _hex_to_rgba,
    _primary_bg_color,
)


def load_font(size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    candidates = [
        Path("C:/Windows/Fonts/segoeui.ttf"),
        Path("C:/Windows/Fonts/arial.ttf"),
        Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"),
        Path("/System/Library/Fonts/Supplemental/Arial.ttf"),
    ]
    for candidate in candidates:
        if candidate.is_file():
            return ImageFont.truetype(str(candidate), size)
    return ImageFont.load_default()


def text_color(brand_data: BrandAnalysis, *, on_light: bool = False) -> tuple[int, int, int, int]:
    if on_light:
        for color in brand_data.colors:
            if color.role == "primary_bg":
                return _hex_to_rgba(color.hex)
        return (26, 26, 26, 255)

    for color in brand_data.colors:
        if color.role == "text":
            return _hex_to_rgba(color.hex)
    for color in brand_data.colors:
        if color.role == "primary_accent":
            return _hex_to_rgba(color.hex)
    return (255, 255, 255, 255)


def extract_logo_rgba(image_path: str, brand_data: BrandAnalysis) -> Image.Image | None:
    path = Path(image_path)
    if not path.is_file():
        return None

    combined_el = _find_element(
        brand_data.elements,
        labels=("combined", "logo", "full_logo"),
        element_type="combined",
    )
    symbol_el = _find_element(
        brand_data.elements,
        labels=("symbol",),
        element_type="symbol",
    )
    logo_el = combined_el or symbol_el or (brand_data.elements[0] if brand_data.elements else None)
    if not logo_el:
        return None

    with Image.open(path) as source:
        crop = _crop_element(source.convert("RGBA"), logo_el)
    return _apply_rembg(crop)


def canvas_background(
    brand_data: BrandAnalysis,
    format_name: str,
    layout: str,
) -> tuple[int, int, int, int]:
    if format_name == "logo_light_bg" or layout == "light":
        return (255, 255, 255, 255)
    return _hex_to_rgba(_primary_bg_color(brand_data))


def fit_logo_with_padding(
    logo: Image.Image,
    canvas_size: tuple[int, int],
    *,
    background: tuple[int, int, int, int],
    vertical_offset_ratio: float = 0.0,
    max_height_ratio: float = 1.0,
) -> Image.Image:
    target_w, target_h = canvas_size
    pad_x = int(target_w * PADDING_RATIO)
    pad_y = int(target_h * PADDING_RATIO)
    inner_w = max(1, target_w - 2 * pad_x)
    inner_h = max(1, int((target_h - 2 * pad_y) * max_height_ratio))

    canvas = Image.new("RGBA", canvas_size, background)
    src = logo.convert("RGBA")
    src_w, src_h = src.size
    if src_w == 0 or src_h == 0:
        return canvas

    scale = min(inner_w / src_w, inner_h / src_h)
    new_w = max(1, int(src_w * scale))
    new_h = max(1, int(src_h * scale))
    resized = src.resize((new_w, new_h), Image.Resampling.LANCZOS)

    offset_x = (target_w - new_w) // 2
    offset_y = pad_y + int((inner_h - new_h) * vertical_offset_ratio)
    canvas.paste(resized, (offset_x, offset_y), resized)
    return canvas
