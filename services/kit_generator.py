"""Pillow-based generation of the 20 brand kit output formats."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Callable

from PIL import Image, ImageDraw, ImageFont

from services.brand_schemas import BrandAnalysis
from services.segmentation import (
    _apply_rembg,
    _crop_element,
    _find_element,
    _hex_to_rgba,
    _primary_bg_color,
    _relative_path,
    generate_isolated_assets,
)

logger = logging.getLogger(__name__)

ProgressCallback = Callable[[str], None]

PADDING_RATIO = 0.15

# All 19 PNG formats + logo_horizontal; BRAND_KIT.md is produced by report_generator.
FORMAT_SPECS: dict[str, dict[str, object]] = {
    # Profiles
    "instagram_profile": {"size": (320, 320), "category": "profiles", "layout": "centered"},
    "tiktok_profile": {"size": (200, 200), "category": "profiles", "layout": "centered"},
    "x_profile": {"size": (400, 400), "category": "profiles", "layout": "centered"},
    "youtube_profile": {"size": (800, 800), "category": "profiles", "layout": "centered"},
    "linkedin_profile": {"size": (300, 300), "category": "profiles", "layout": "centered"},
    "favicon": {"size": (32, 32), "category": "profiles", "layout": "centered"},
    "app_icon": {"size": (1024, 1024), "category": "profiles", "layout": "centered"},
    # Banners
    "x_header": {"size": (1500, 500), "category": "banners", "layout": "banner"},
    "youtube_banner": {"size": (2560, 1440), "category": "banners", "layout": "banner"},
    "linkedin_banner": {"size": (1128, 191), "category": "banners", "layout": "banner"},
    "facebook_cover": {"size": (820, 312), "category": "banners", "layout": "banner"},
    # Posts
    "instagram_post": {"size": (1080, 1080), "category": "posts", "layout": "centered"},
    "instagram_story": {"size": (1080, 1920), "category": "posts", "layout": "vertical"},
    "tiktok_cover": {"size": (1080, 1920), "category": "posts", "layout": "vertical"},
    # Isolated assets
    "symbol_transparent": {"size": (1000, 1000), "category": "isolated", "layout": "isolated"},
    "wordmark_transparent": {"size": (2000, 500), "category": "isolated", "layout": "isolated"},
    "logo_dark_bg": {"size": (1000, 1000), "category": "isolated", "layout": "isolated"},
    "logo_light_bg": {"size": (1000, 1000), "category": "isolated", "layout": "isolated"},
    "logo_horizontal": {"size": (2000, 600), "category": "isolated", "layout": "horizontal"},
}

ALL_FORMAT_NAMES: list[str] = list(FORMAT_SPECS.keys())
ISOLATED_FORMAT_NAMES = frozenset(
    name for name, spec in FORMAT_SPECS.items() if spec["category"] == "isolated"
)


def _load_font(size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
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


def _text_color(brand_data: BrandAnalysis, *, on_light: bool = False) -> tuple[int, int, int, int]:
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


def _extract_logo_rgba(image_path: str, brand_data: BrandAnalysis) -> Image.Image | None:
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


def _canvas_background(
    brand_data: BrandAnalysis,
    format_name: str,
    layout: str,
) -> tuple[int, int, int, int]:
    if format_name == "logo_light_bg" or layout == "light":
        return (255, 255, 255, 255)
    return _hex_to_rgba(_primary_bg_color(brand_data))


def _fit_logo_with_padding(
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


def _render_banner(
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
    title_font = _load_font(title_size)
    subtitle_font = _load_font(subtitle_size)
    text_rgba = _text_color(brand_data)

    brand_name = brand_data.brand_name.strip() or "Brand"
    tagline = (brand_data.tagline or "").strip()

    if logo:
        logo_area_w = int(width * 0.35)
        logo_area_h = int(height * 0.8)
        logo_canvas = _fit_logo_with_padding(
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


def _render_vertical_post(
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
        logo_canvas = _fit_logo_with_padding(
            logo,
            (width, logo_zone_h),
            background=background,
            vertical_offset_ratio=0.5,
        )
        canvas.paste(logo_canvas, (0, 0), logo_canvas)

    draw = ImageDraw.Draw(canvas)
    accent = _text_color(brand_data)
    hint_font = _load_font(max(14, width // 40))
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


def _render_horizontal_logo(
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
            logo = _extract_logo_rgba(image_path, brand_data)
            if logo:
                parts.append(logo)

    if not parts:
        return canvas

    target_w, target_h = canvas_size
    pad = int(min(target_w, target_h) * PADDING_RATIO)
    inner_h = target_h - 2 * pad
    inner_w = target_w - 2 * pad

    if len(parts) == 1:
        fitted = _fit_logo_with_padding(parts[0], (inner_w, inner_h), background=background)
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


def _render_format(
    format_name: str,
    image_path: str,
    brand_data: BrandAnalysis,
    logo: Image.Image | None,
) -> Image.Image:
    spec = FORMAT_SPECS[format_name]
    size = spec["size"]  # type: ignore[assignment]
    layout = spec["layout"]  # type: ignore[assignment]
    assert isinstance(size, tuple)
    assert isinstance(layout, str)

    background = _canvas_background(brand_data, format_name, layout)

    if layout == "banner":
        return _render_banner(logo, size, brand_data, background=background)
    if layout == "vertical":
        return _render_vertical_post(logo, size, brand_data, background=background)
    if layout == "horizontal":
        return _render_horizontal_logo(image_path, brand_data, size, background=background)
    if format_name == "logo_light_bg":
        background = (255, 255, 255, 255)

    if logo is None:
        return Image.new("RGBA", size, background)

    max_height_ratio = 1.0
    vertical_offset = 0.0
    if layout == "vertical":
        max_height_ratio = 0.45
        vertical_offset = 0.5

    return _fit_logo_with_padding(
        logo,
        size,
        background=background,
        vertical_offset_ratio=vertical_offset,
        max_height_ratio=max_height_ratio,
    )


def generate_full_kit(
    image_path: str,
    brand_data: BrandAnalysis,
    output_dir: str,
    formats: list[str] | None = None,
    *,
    on_progress: ProgressCallback | None = None,
) -> dict[str, str]:
    """Generate all requested kit formats and return {format_name: repo_relative_path}."""
    path = Path(image_path)
    if not path.is_file():
        raise FileNotFoundError(f"Image introuvable: {image_path}")

    out_dir = Path(output_dir)
    formats_dir = out_dir / "formats"
    isolated_dir = out_dir / "isolated"
    formats_dir.mkdir(parents=True, exist_ok=True)
    isolated_dir.mkdir(parents=True, exist_ok=True)

    requested = formats if formats else ALL_FORMAT_NAMES
    unknown = [name for name in requested if name not in FORMAT_SPECS]
    if unknown:
        raise ValueError(f"Formats inconnus: {', '.join(unknown)}")

    results: dict[str, str] = {}
    logo = _extract_logo_rgba(str(path), brand_data)

    isolated_requested = [name for name in requested if name in ISOLATED_FORMAT_NAMES]
    social_requested = [name for name in requested if name not in ISOLATED_FORMAT_NAMES]

    if isolated_requested:
        if on_progress:
            on_progress("isolated_assets")
        try:
            isolated_results = generate_isolated_assets(
                str(path),
                brand_data,
                str(isolated_dir),
            )
            for name in isolated_requested:
                if name in isolated_results:
                    results[name] = isolated_results[name]
                elif name == "logo_horizontal":
                    if on_progress:
                        on_progress(name)
                    img = _render_horizontal_logo(
                        str(path),
                        brand_data,
                        FORMAT_SPECS["logo_horizontal"]["size"],  # type: ignore[arg-type]
                        background=_canvas_background(brand_data, name, "horizontal"),
                    )
                    out_path = isolated_dir / f"{name}.png"
                    img.save(out_path, format="PNG")
                    results[name] = _relative_path(out_path)
        except Exception:
            logger.exception("Isolated asset generation failed")

    for format_name in social_requested:
        if on_progress:
            on_progress(format_name)
        try:
            img = _render_format(format_name, str(path), brand_data, logo)
            out_path = formats_dir / f"{format_name}.png"
            img.save(out_path, format="PNG")
            results[format_name] = _relative_path(out_path)
        except Exception:
            logger.exception("Format generation failed for %s", format_name)

    return results
