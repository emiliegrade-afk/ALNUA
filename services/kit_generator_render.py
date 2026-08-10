"""Pillow rendering helpers for brand kit formats."""

from __future__ import annotations

from PIL import Image

from services.brand_schemas import BrandAnalysis
from services.kit_generator_render_layouts import (
    render_banner,
    render_horizontal_logo,
    render_vertical_post,
)
from services.kit_generator_render_utils import (
    canvas_background,
    extract_logo_rgba,
    fit_logo_with_padding,
    load_font,
    text_color,
)

__all__ = [
    "load_font",
    "text_color",
    "extract_logo_rgba",
    "canvas_background",
    "fit_logo_with_padding",
    "render_banner",
    "render_vertical_post",
    "render_horizontal_logo",
    "render_format",
]


def render_format(
    format_name: str,
    image_path: str,
    brand_data: BrandAnalysis,
    logo: Image.Image | None,
    *,
    format_specs: dict[str, dict[str, object]],
) -> Image.Image:
    spec = format_specs[format_name]
    size = spec["size"]  # type: ignore[assignment]
    layout = spec["layout"]  # type: ignore[assignment]
    assert isinstance(size, tuple)
    assert isinstance(layout, str)

    background = canvas_background(brand_data, format_name, layout)

    if layout == "banner":
        return render_banner(logo, size, brand_data, background=background)
    if layout == "vertical":
        return render_vertical_post(logo, size, brand_data, background=background)
    if layout == "horizontal":
        return render_horizontal_logo(image_path, brand_data, size, background=background)
    if format_name == "logo_light_bg":
        background = (255, 255, 255, 255)

    if logo is None:
        return Image.new("RGBA", size, background)

    max_height_ratio = 1.0
    vertical_offset = 0.0
    if layout == "vertical":
        max_height_ratio = 0.45
        vertical_offset = 0.5

    return fit_logo_with_padding(
        logo,
        size,
        background=background,
        vertical_offset_ratio=vertical_offset,
        max_height_ratio=max_height_ratio,
    )
