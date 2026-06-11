"""OpenCV crop execution from normalized bounding boxes — no second-guessing."""

from __future__ import annotations

import io
import logging
import re
from pathlib import Path

import cv2
import numpy as np
from PIL import Image
from rembg import remove

from services.brand_schemas import BrandAnalysis, BrandElement, BoundingBox

logger = logging.getLogger(__name__)

# Spec: 5% margin; panel snap handles grid sheets so margin stays small on snapped boxes.
MARGIN_RATIO = 0.05
PANEL_SNAP_MARGIN = 0.02
ISOLATED_ASSETS: dict[str, tuple[int, int]] = {
    "symbol_transparent": (1000, 1000),
    "wordmark_transparent": (2000, 500),
    "logo_dark_bg": (1000, 1000),
    "logo_light_bg": (1000, 1000),
}


def _hex_to_rgba(hex_color: str, alpha: int = 255) -> tuple[int, int, int, int]:
    cleaned = hex_color.strip().lstrip("#").upper()
    if len(cleaned) == 3:
        cleaned = "".join(ch * 2 for ch in cleaned)
    return (
        int(cleaned[0:2], 16),
        int(cleaned[2:4], 16),
        int(cleaned[4:6], 16),
        alpha,
    )


def _sanitize_label(label: str) -> str:
    cleaned = re.sub(r"[^\w\-]+", "_", label.strip().lower())
    return cleaned or "element"


def _normalize_bbox(bbox: BoundingBox) -> BoundingBox:
    """Ensure x1<x2, y1<y2 and values stay in 0-1000."""
    x1, x2 = sorted((bbox.x1, bbox.x2))
    y1, y2 = sorted((bbox.y1, bbox.y2))
    return BoundingBox(
        x1=max(0, min(1000, x1)),
        y1=max(0, min(1000, y1)),
        x2=max(0, min(1000, x2)),
        y2=max(0, min(1000, y2)),
    )


def _bbox_to_pixel_box(
    bbox: BoundingBox,
    img_width: int,
    img_height: int,
) -> tuple[int, int, int, int]:
    """Convert normalized 0-1000 bbox to pixel coords with margin."""
    normalized = _normalize_bbox(bbox)
    x1 = normalized.x1 * img_width / 1000
    y1 = normalized.y1 * img_height / 1000
    x2 = normalized.x2 * img_width / 1000
    y2 = normalized.y2 * img_height / 1000

    box_w = max(1.0, x2 - x1)
    box_h = max(1.0, y2 - y1)
    margin_x = box_w * MARGIN_RATIO
    margin_y = box_h * MARGIN_RATIO

    left = max(0, int(round(x1 - margin_x)))
    top = max(0, int(round(y1 - margin_y)))
    right = min(img_width, int(round(x2 + margin_x)))
    bottom = min(img_height, int(round(y2 + margin_y)))

    if right <= left:
        right = min(img_width, left + 1)
    if bottom <= top:
        bottom = min(img_height, top + 1)

    return left, top, right, bottom


def _panel_aspect_category(aspect: float) -> str:
    if aspect >= 0.62:
        return "post"
    if aspect >= 0.38:
        return "story"
    return "wide"


def _dedupe_panels(
    panels: list[tuple[int, int, int, int, float]],
) -> list[tuple[int, int, int, int, float]]:
    """Keep the tightest rectangle when OpenCV finds nested quads."""
    if not panels:
        return []
    panels.sort(key=lambda p: (p[2] - p[0]) * (p[3] - p[1]))
    kept: list[tuple[int, int, int, int, float]] = []
    for panel in panels:
        l, t, r, b, asp = panel
        dominated = False
        for kl, kt, kr, kb, _ in kept:
            if l >= kl and t >= kt and r <= kr and b <= kb:
                dominated = True
                break
        if not dominated:
            kept.append(panel)
    return kept


def _detect_panels(image: Image.Image) -> list[tuple[int, int, int, int, float]]:
    """Find bordered template panels on brand guideline sheets."""
    arr = np.array(image.convert("RGB"))
    gray = cv2.cvtColor(arr, cv2.COLOR_RGB2GRAY)
    blur = cv2.GaussianBlur(gray, (3, 3), 0)
    edges = cv2.Canny(blur, 40, 120)
    edges = cv2.dilate(edges, np.ones((2, 2), np.uint8), iterations=1)

    contours, _ = cv2.findContours(edges, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
    img_h, img_w = gray.shape
    raw: list[tuple[int, int, int, int, float]] = []

    for contour in contours:
        peri = cv2.arcLength(contour, True)
        approx = cv2.approxPolyDP(contour, 0.02 * peri, True)
        if len(approx) != 4:
            continue
        x, y, bw, bh = cv2.boundingRect(approx)
        area = bw * bh
        if area < 12_000 or area > img_w * img_h * 0.1:
            continue
        aspect = bw / max(bh, 1)
        if aspect < 0.35 or aspect > 0.95 or bh < 160:
            continue
        raw.append((x, y, x + bw, y + bh, aspect))

    return _dedupe_panels(raw)


def _extract_label_index(label: str) -> int | None:
    lowered = label.lower()
    patterns = [
        r"story\s*0*(\d+)",
        r"post\s*0*(\d+)",
        r"reel\s*0*(\d+)",
        r"cover\s*0*(\d+)",
        r"template\s*0*(\d+)",
        r"\b0*(\d+)\b",
    ]
    for pattern in patterns:
        match = re.search(pattern, lowered)
        if match:
            return int(match.group(1))
    return None


def _group_panels_by_row(
    panels: list[tuple[int, int, int, int, float]],
) -> list[list[tuple[int, int, int, int, float]]]:
    if not panels:
        return []
    sorted_panels = sorted(panels, key=lambda p: (p[1], p[0]))
    rows: list[list[tuple[int, int, int, int, float]]] = []
    for panel in sorted_panels:
        _, top, _, bottom, _ = panel
        center_y = (top + bottom) / 2
        placed = False
        for row in rows:
            row_center = sum((p[1] + p[3]) / 2 for p in row) / len(row)
            if abs(center_y - row_center) < 50:
                row.append(panel)
                placed = True
                break
        if not placed:
            rows.append([panel])
    for row in rows:
        row.sort(key=lambda p: p[0])
    return rows


def _snap_box_to_panel(
    image: Image.Image,
    element: BrandElement,
    panels: list[tuple[int, int, int, int, float]],
) -> tuple[int, int, int, int] | None:
    """Snap LLM hint to the nearest detected grid panel."""
    if not panels:
        return None

    width, height = image.size
    llm_box = _bbox_to_pixel_box(element.bbox, width, height)
    llm_cx = (llm_box[0] + llm_box[2]) / 2
    llm_cy = (llm_box[1] + llm_box[3]) / 2
    llm_w = llm_box[2] - llm_box[0]
    llm_h = llm_box[3] - llm_box[1]
    llm_aspect = llm_w / max(llm_h, 1)

    label_index = _extract_label_index(element.label)
    rows = _group_panels_by_row(panels)

    # Label says "Story 01" → pick 1st panel in the story row closest to LLM y.
    if label_index is not None:
        hint_category = _panel_aspect_category(llm_aspect)
        if "story" in element.label.lower():
            hint_category = "story"
        elif "post" in element.label.lower():
            hint_category = "post"
        elif "reel" in element.label.lower() or "cover" in element.label.lower():
            hint_category = "story"

        best_row: list[tuple[int, int, int, int, float]] | None = None
        best_row_dist = float("inf")
        for row in rows:
            if not row:
                continue
            row_cy = sum((p[1] + p[3]) / 2 for p in row) / len(row)
            row_asp = sum(p[4] for p in row) / len(row)
            row_cat = _panel_aspect_category(row_asp)
            if row_cat != hint_category and hint_category != "wide":
                continue
            dist = abs(row_cy - llm_cy)
            if dist < best_row_dist:
                best_row_dist = dist
                best_row = row

        if best_row and 1 <= label_index <= len(best_row):
            panel = best_row[label_index - 1]
            return panel[0], panel[1], panel[2], panel[3]

    # Fallback: nearest panel center to LLM center.
    best_panel = None
    best_dist = float("inf")
    for left, top, right, bottom, _ in panels:
        cx = (left + right) / 2
        cy = (top + bottom) / 2
        dist = ((cx - llm_cx) ** 2 + (cy - llm_cy) ** 2) ** 0.5
        if dist < best_dist:
            best_dist = dist
            best_panel = (left, top, right, bottom)

    if best_panel and best_dist < max(width, height) * 0.25:
        return best_panel
    return None


def _apply_margin_to_box(
    box: tuple[int, int, int, int],
    img_width: int,
    img_height: int,
    *,
    margin_ratio: float = PANEL_SNAP_MARGIN,
) -> tuple[int, int, int, int]:
    left, top, right, bottom = box
    box_w = max(1, right - left)
    box_h = max(1, bottom - top)
    margin_x = box_w * margin_ratio
    margin_y = box_h * margin_ratio
    return (
        max(0, int(round(left - margin_x))),
        max(0, int(round(top - margin_y))),
        min(img_width, int(round(right + margin_x))),
        min(img_height, int(round(bottom + margin_y))),
    )


def _crop_element(
    image: Image.Image,
    element: BrandElement,
    *,
    panels: list[tuple[int, int, int, int, float]] | None = None,
    use_panel_snap: bool = True,
) -> Image.Image:
    """Crop using panel snap on grid sheets, LLM bbox as fallback."""
    width, height = image.size
    if use_panel_snap:
        snapped = _snap_box_to_panel(image, element, panels or [])
        if snapped:
            box = _apply_margin_to_box(snapped, width, height)
            return image.crop(box)
    box = _bbox_to_pixel_box(element.bbox, width, height)
    return image.crop(box)


def _apply_rembg(image: Image.Image) -> Image.Image:
    buffer = io.BytesIO()
    image.convert("RGBA").save(buffer, format="PNG")
    result_bytes = remove(buffer.getvalue())
    return Image.open(io.BytesIO(result_bytes)).convert("RGBA")


def _tighten_transparent_crop(image: Image.Image) -> Image.Image:
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


def _fit_on_canvas(
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


def _relative_path(file_path: Path) -> str:
    repo_root = Path(__file__).resolve().parent.parent
    return str(file_path.relative_to(repo_root)).replace("\\", "/")


def _find_element(
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


def _primary_bg_color(brand_data: BrandAnalysis) -> str:
    for color in brand_data.colors:
        if color.role == "primary_bg":
            return color.hex
    if brand_data.colors:
        return brand_data.colors[0].hex
    return "#1A1A1A"


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
        panels = _detect_panels(image) if use_panel_snap else []

        for element in elements:
            if labels_filter is not None and element.label not in labels_filter:
                continue
            try:
                crop = _crop_element(
                    image,
                    element,
                    panels=panels,
                    use_panel_snap=use_panel_snap,
                )
                # rembg only for isolated symbols — not templates/combined on brand sheets
                if element.type == "symbol":
                    crop = _tighten_transparent_crop(_apply_rembg(crop))

                existing_rel = results.get(element.label)
                if existing_rel:
                    output_path = repo_root / existing_rel.replace("\\", "/")
                else:
                    filename = _sanitize_label(element.label)
                    if filename in used_names:
                        filename = f"{filename}_{len(used_names)}"
                    used_names.add(filename)
                    output_path = out_dir / f"{filename}.png"

                output_path.parent.mkdir(parents=True, exist_ok=True)
                crop.save(output_path, format="PNG")
                results[element.label] = _relative_path(output_path)
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

    symbol_el = _find_element(
        brand_data.elements,
        labels=("symbol",),
        element_type="symbol",
    )
    wordmark_el = _find_element(
        brand_data.elements,
        labels=("wordmark",),
        element_type="text",
    )
    combined_el = _find_element(
        brand_data.elements,
        labels=("combined", "logo", "full_logo"),
        element_type="combined",
    )

    primary_bg = _primary_bg_color(brand_data)
    results: dict[str, str] = {}

    with Image.open(path) as source:
        image = source.convert("RGBA")
        panels = _detect_panels(image) if use_panel_snap else []

        if symbol_el:
            symbol_crop = _crop_element(
                image,
                symbol_el,
                panels=panels,
                use_panel_snap=use_panel_snap,
            )
            symbol_transparent = _tighten_transparent_crop(_apply_rembg(symbol_crop))
            symbol_canvas = _fit_on_canvas(
                symbol_transparent,
                ISOLATED_ASSETS["symbol_transparent"],
            )
            symbol_path = out_dir / "symbol_transparent.png"
            symbol_canvas.save(symbol_path, format="PNG")
            results["symbol_transparent"] = _relative_path(symbol_path)

        if wordmark_el:
            wordmark_crop = _crop_element(
                image,
                wordmark_el,
                panels=panels,
                use_panel_snap=use_panel_snap,
            )
            wordmark_transparent = _tighten_transparent_crop(_apply_rembg(wordmark_crop))
            wordmark_canvas = _fit_on_canvas(
                wordmark_transparent,
                ISOLATED_ASSETS["wordmark_transparent"],
            )
            wordmark_path = out_dir / "wordmark_transparent.png"
            wordmark_canvas.save(wordmark_path, format="PNG")
            results["wordmark_transparent"] = _relative_path(wordmark_path)

        logo_source_el = combined_el or symbol_el or (brand_data.elements[0] if brand_data.elements else None)
        if logo_source_el:
            logo_crop = _crop_element(
                image,
                logo_source_el,
                panels=panels,
                use_panel_snap=use_panel_snap,
            )
            logo_rgba = _tighten_transparent_crop(_apply_rembg(logo_crop))

            dark_canvas = _fit_on_canvas(
                logo_rgba,
                ISOLATED_ASSETS["logo_dark_bg"],
                background=_hex_to_rgba(primary_bg),
            )
            dark_path = out_dir / "logo_dark_bg.png"
            dark_canvas.save(dark_path, format="PNG")
            results["logo_dark_bg"] = _relative_path(dark_path)

            light_canvas = _fit_on_canvas(
                logo_rgba,
                ISOLATED_ASSETS["logo_light_bg"],
                background=(255, 255, 255, 255),
            )
            light_path = out_dir / "logo_light_bg.png"
            light_canvas.save(light_path, format="PNG")
            results["logo_light_bg"] = _relative_path(light_path)

    return results
