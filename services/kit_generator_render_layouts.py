"""Brand kit rendering — banner and composite layout helpers."""

from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw

from services.brand_schemas import BrandAnalysis
from services.kit_generator_render_utils import (
    extract_logo_rgba,
    fit_logo_with_padding,
    load_font,
    text_color,
)
from services.kit_generator_specs import PADDING_RATIO
from services.segmentation import (
    _apply_rembg,
    _crop_element,
    _find_element,
)


def render_banner(
    logo: Image.Image | None,
    canvas_size: tuple[int, int],
    brand_data: BrandAnalysis,
    *,
    background: tuple[int, int, int, int],
) -> Image.Image:
    canvas = Image.new("RGBA", canvas_size, background)
    draw = ImageDraw.Draw(canvas)
    width, height = canvas_size

    title_size = max(18, height // 6)
    subtitle_size = max(12, height // 10)
    title_font = load_font(title_size)
    subtitle_font = load_font(subtitle_size)
    text_rgba = text_color(brand_data)

    brand_name = brand_data.brand_name.strip() or "Brand"
    tagline = (brand_data.tagline or "").strip()

    if logo:
        logo_area_w = int(width * 0.35)
        logo_area_h = int(height * 0.8)
        logo_canvas = fit_logo_with_padding(
            logo,
            (logo_area_w, logo_area_h),
            background=(0, 0, 0, 0),
        )
        canvas.paste(logo_canvas, (int(width * 0.06), (height - logo_area_h) // 2), logo_canvas)

    text_x = int(width * 0.42) if logo else int(width * 0.08)
    text_y = height // 2 - (title_size // 2)
    if tagline:
        text_y -= subtitle_size // 2
    else:
        text_y = (height - title_size) // 2

    draw.text((text_x, text_y), brand_name, fill=text_rgba, font=title_font)
    if tagline:
        draw.text(
            (text_x, text_y + title_size + 4),
            tagline,
            fill=(*text_rgba[:3], min(220, text_rgba[3])),
            font=subtitle_font,
        )

    return canvas


def render_vertical_post(
    logo: Image.Image | None,
    canvas_size: tuple[int, int],
    brand_data: BrandAnalysis,
    *,
    background: tuple[int, int, int, int],
) -> Image.Image:
    """Vertical layout: logo in upper area, lower ~45% reserved for overlay text."""
    width, height = canvas_size
    canvas = Image.new("RGBA", canvas_size, background)

    if logo:
        logo_zone_h = int(height * 0.45)
        logo_canvas = fit_logo_with_padding(
            logo,
            (width, logo_zone_h),
            background=background,
            vertical_offset_ratio=0.5,
        )
        canvas.paste(logo_canvas, (0, 0), logo_canvas)

    draw = ImageDraw.Draw(canvas)
    accent = text_color(brand_data)
    hint_font = load_font(max(14, width // 40))
    hint = brand_data.brand_name
    if brand_data.tagline:
        hint = f"{hint} — {brand_data.tagline}"
    bbox = draw.textbbox((0, 0), hint, font=hint_font)
    text_w = bbox[2] - bbox[0]
    draw.text(
        ((width - text_w) // 2, int(height * 0.52)),
        hint,
        fill=(*accent[:3], 180),
        font=hint_font,
    )

    return canvas


def render_horizontal_logo(
    image_path: str,
    brand_data: BrandAnalysis,
    canvas_size: tuple[int, int],
    *,
    background: tuple[int, int, int, int],
) -> Image.Image:
    path = Path(image_path)
    canvas = Image.new("RGBA", canvas_size, background)
    if not path.is_file():
        return canvas

    symbol_el = _find_element(brand_data.elements, labels=("symbol",), element_type="symbol")
    wordmark_el = _find_element(brand_data.elements, labels=("wordmark",), element_type="text")
    combined_el = _find_element(
        brand_data.elements,
        labels=("combined", "logo", "full_logo"),
        element_type="combined",
    )

    with Image.open(path) as source:
        image = source.convert("RGBA")
        parts: list[Image.Image] = []

        if symbol_el and wordmark_el:
            parts.append(_apply_rembg(_crop_element(image, symbol_el)))
            parts.append(_apply_rembg(_crop_element(image, wordmark_el)))
        elif combined_el:
            parts.append(_apply_rembg(_crop_element(image, combined_el)))
        else:
            logo = extract_logo_rgba(image_path, brand_data)
            if logo:
                parts.append(logo)

    if not parts:
        return canvas

    target_w, target_h = canvas_size
    pad = int(min(target_w, target_h) * PADDING_RATIO)
    inner_h = target_h - 2 * pad
    inner_w = target_w - 2 * pad

    if len(parts) == 1:
        fitted = fit_logo_with_padding(parts[0], (inner_w, inner_h), background=background)
        canvas.paste(fitted, (pad, pad), fitted)
        return canvas

    symbol, wordmark = parts[0], parts[1]
    sym_max_w = int(inner_w * 0.28)
    sym_scale = min(sym_max_w / max(symbol.width, 1), inner_h / max(symbol.height, 1))
    sym_w = max(1, int(symbol.width * sym_scale))
    sym_h = max(1, int(symbol.height * sym_scale))
    symbol_resized = symbol.resize((sym_w, sym_h), Image.Resampling.LANCZOS)

    gap = int(inner_w * 0.04)
    word_max_w = inner_w - sym_w - gap
    wm_scale = min(word_max_w / max(wordmark.width, 1), inner_h / max(wordmark.height, 1))
    wm_w = max(1, int(wordmark.width * wm_scale))
    wm_h = max(1, int(wordmark.height * wm_scale))
    wordmark_resized = wordmark.resize((wm_w, wm_h), Image.Resampling.LANCZOS)

    total_w = sym_w + gap + wm_w
    start_x = pad + (inner_w - total_w) // 2
    sym_y = pad + (inner_h - sym_h) // 2
    wm_y = pad + (inner_h - wm_h) // 2

    canvas.paste(symbol_resized, (start_x, sym_y), symbol_resized)
    canvas.paste(wordmark_resized, (start_x + sym_w + gap, wm_y), wordmark_resized)
    return canvas
