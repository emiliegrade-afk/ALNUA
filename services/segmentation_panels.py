"""Brand segmentation — grid panel detection and LLM bbox snap."""
from __future__ import annotations

import re

import cv2
import numpy as np
from PIL import Image

from services.brand_schemas import BrandElement
from services.segmentation_bbox import apply_margin_to_box, bbox_to_pixel_box


def panel_aspect_category(aspect: float) -> str:
    if aspect >= 0.62:
        return "post"
    if aspect >= 0.38:
        return "story"
    return "wide"


def dedupe_panels(
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


def detect_panels(image: Image.Image) -> list[tuple[int, int, int, int, float]]:
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

    return dedupe_panels(raw)


def extract_label_index(label: str) -> int | None:
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


def group_panels_by_row(
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


def snap_box_to_panel(
    image: Image.Image,
    element: BrandElement,
    panels: list[tuple[int, int, int, int, float]],
) -> tuple[int, int, int, int] | None:
    """Snap LLM hint to the nearest detected grid panel."""
    if not panels:
        return None

    width, height = image.size
    llm_box = bbox_to_pixel_box(element.bbox, width, height)
    llm_cx = (llm_box[0] + llm_box[2]) / 2
    llm_cy = (llm_box[1] + llm_box[3]) / 2
    llm_w = llm_box[2] - llm_box[0]
    llm_h = llm_box[3] - llm_box[1]
    llm_aspect = llm_w / max(llm_h, 1)

    label_index = extract_label_index(element.label)
    rows = group_panels_by_row(panels)

    if label_index is not None:
        hint_category = panel_aspect_category(llm_aspect)
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
            row_cat = panel_aspect_category(row_asp)
            if row_cat != hint_category and hint_category != "wide":
                continue
            dist = abs(row_cy - llm_cy)
            if dist < best_row_dist:
                best_row_dist = dist
                best_row = row

        if best_row and 1 <= label_index <= len(best_row):
            panel = best_row[label_index - 1]
            return panel[0], panel[1], panel[2], panel[3]

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


def crop_element(
    image: Image.Image,
    element: BrandElement,
    *,
    panels: list[tuple[int, int, int, int, float]] | None = None,
    use_panel_snap: bool = True,
) -> Image.Image:
    """Crop using panel snap on grid sheets, LLM bbox as fallback."""
    width, height = image.size
    if use_panel_snap:
        snapped = snap_box_to_panel(image, element, panels or [])
        if snapped:
            box = apply_margin_to_box(snapped, width, height)
            return image.crop(box)
    box = bbox_to_pixel_box(element.bbox, width, height)
    return image.crop(box)
