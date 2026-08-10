"""OpenCV crop execution from normalized bounding boxes — no second-guessing.

Façade : siblings under ``services/segmentation_*.py`` keep each module ≤ ~300 lines.
"""

from __future__ import annotations

import logging
from pathlib import Path

from PIL import Image

from services.brand_schemas import BrandAnalysis, BrandElement
from services.segmentation_bbox import ISOLATED_ASSETS, hex_to_rgba, sanitize_label
from services.segmentation_image import (
    apply_rembg,
    find_element,
    fit_on_canvas,
    primary_bg_color,
    relative_path,
    tighten_transparent_crop,
)
from services.segmentation_panels import crop_element, detect_panels

logger = logging.getLogger(__name__)

# kit_generator.py imports these private helpers — preserve underscore names
_apply_rembg = apply_rembg
_crop_element = crop_element
_find_element = find_element
_hex_to_rgba = hex_to_rgba
_primary_bg_color = primary_bg_color
_relative_path = relative_path


def segment_elements(
    image_path: str,
    elements: list[BrandElement],
    *,
    segments_dir: str,
    use_panel_snap: bool = True,
    labels_filter: set[str] | None = None,
    existing_paths: dict[str, str] | None = None,
) -> dict[str, str]:
    """Crop each detected element; optional partial refine keeps prior segment paths."""
    path = Path(image_path)
    if not path.is_file():
        raise FileNotFoundError(f"Image introuvable: {image_path}")

    out_dir = Path(segments_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    repo_root = Path(__file__).resolve().parent.parent
    results: dict[str, str] = dict(existing_paths or {})
    used_names: set[str] = set()
    for rel in results.values():
        used_names.add(Path(rel).stem)

    with Image.open(path) as source:
        image = source.convert("RGBA")
        panels = detect_panels(image) if use_panel_snap else []

        for element in elements:
            if labels_filter is not None and element.label not in labels_filter:
                continue
            try:
                crop = crop_element(
                    image,
                    element,
                    panels=panels,
                    use_panel_snap=use_panel_snap,
                )
                if element.type == "symbol":
                    crop = tighten_transparent_crop(apply_rembg(crop))

                existing_rel = results.get(element.label)
                if existing_rel:
                    output_path = repo_root / existing_rel.replace("\\", "/")
                else:
                    filename = sanitize_label(element.label)
                    if filename in used_names:
                        filename = f"{filename}_{len(used_names)}"
                    used_names.add(filename)
                    output_path = out_dir / f"{filename}.png"

                output_path.parent.mkdir(parents=True, exist_ok=True)
                crop.save(output_path, format="PNG")
                results[element.label] = relative_path(output_path)
            except Exception:
                logger.exception("Segmentation failed for element %s", element.label)

    return results


def generate_isolated_assets(
    image_path: str,
    brand_data: BrandAnalysis,
    output_dir: str,
    *,
    use_panel_snap: bool = True,
) -> dict[str, str]:
    """Build the four isolated brand assets defined in the spec."""
    path = Path(image_path)
    if not path.is_file():
        raise FileNotFoundError(f"Image introuvable: {image_path}")

    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    symbol_el = find_element(
        brand_data.elements,
        labels=("symbol",),
        element_type="symbol",
    )
    wordmark_el = find_element(
        brand_data.elements,
        labels=("wordmark",),
        element_type="text",
    )
    combined_el = find_element(
        brand_data.elements,
        labels=("combined", "logo", "full_logo"),
        element_type="combined",
    )

    primary_bg = primary_bg_color(brand_data)
    results: dict[str, str] = {}

    with Image.open(path) as source:
        image = source.convert("RGBA")
        panels = detect_panels(image) if use_panel_snap else []

        if symbol_el:
            symbol_crop = crop_element(
                image,
                symbol_el,
                panels=panels,
                use_panel_snap=use_panel_snap,
            )
            symbol_transparent = tighten_transparent_crop(apply_rembg(symbol_crop))
            symbol_canvas = fit_on_canvas(
                symbol_transparent,
                ISOLATED_ASSETS["symbol_transparent"],
            )
            symbol_path = out_dir / "symbol_transparent.png"
            symbol_canvas.save(symbol_path, format="PNG")
            results["symbol_transparent"] = relative_path(symbol_path)

        if wordmark_el:
            wordmark_crop = crop_element(
                image,
                wordmark_el,
                panels=panels,
                use_panel_snap=use_panel_snap,
            )
            wordmark_transparent = tighten_transparent_crop(apply_rembg(wordmark_crop))
            wordmark_canvas = fit_on_canvas(
                wordmark_transparent,
                ISOLATED_ASSETS["wordmark_transparent"],
            )
            wordmark_path = out_dir / "wordmark_transparent.png"
            wordmark_canvas.save(wordmark_path, format="PNG")
            results["wordmark_transparent"] = relative_path(wordmark_path)

        logo_source_el = combined_el or symbol_el or (brand_data.elements[0] if brand_data.elements else None)
        if logo_source_el:
            logo_crop = crop_element(
                image,
                logo_source_el,
                panels=panels,
                use_panel_snap=use_panel_snap,
            )
            logo_rgba = tighten_transparent_crop(apply_rembg(logo_crop))

            dark_canvas = fit_on_canvas(
                logo_rgba,
                ISOLATED_ASSETS["logo_dark_bg"],
                background=hex_to_rgba(primary_bg),
            )
            dark_path = out_dir / "logo_dark_bg.png"
            dark_canvas.save(dark_path, format="PNG")
            results["logo_dark_bg"] = relative_path(dark_path)

            light_canvas = fit_on_canvas(
                logo_rgba,
                ISOLATED_ASSETS["logo_light_bg"],
                background=(255, 255, 255, 255),
            )
            light_path = out_dir / "logo_light_bg.png"
            light_canvas.save(light_path, format="PNG")
            results["logo_light_bg"] = relative_path(light_path)

    return results
