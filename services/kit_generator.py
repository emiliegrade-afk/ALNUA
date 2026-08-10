"""Pillow-based generation of the 20 brand kit output formats."""

from __future__ import annotations

import logging
from collections.abc import Callable
from pathlib import Path

from services.brand_schemas import BrandAnalysis
from services.kit_generator_render import (
    canvas_background,
    extract_logo_rgba,
    render_format,
    render_horizontal_logo,
)
from services.kit_generator_specs import (
    ALL_FORMAT_NAMES,
    FORMAT_SPECS,
    ISOLATED_FORMAT_NAMES,
)
from services.segmentation import _relative_path, generate_isolated_assets

logger = logging.getLogger(__name__)

ProgressCallback = Callable[[str], None]

__all__ = [
    "ALL_FORMAT_NAMES",
    "FORMAT_SPECS",
    "ISOLATED_FORMAT_NAMES",
    "generate_full_kit",
]


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
    logo = extract_logo_rgba(str(path), brand_data)

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
                    img = render_horizontal_logo(
                        str(path),
                        brand_data,
                        FORMAT_SPECS["logo_horizontal"]["size"],  # type: ignore[arg-type]
                        background=canvas_background(brand_data, name, "horizontal"),
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
            img = render_format(
                format_name,
                str(path),
                brand_data,
                logo,
                format_specs=FORMAT_SPECS,
            )
            out_path = formats_dir / f"{format_name}.png"
            img.save(out_path, format="PNG")
            results[format_name] = _relative_path(out_path)
        except Exception:
            logger.exception("Format generation failed for %s", format_name)

    return results
