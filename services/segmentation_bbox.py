"""Brand segmentation — bbox constants and pixel conversion."""
from __future__ import annotations

import re

from services.brand_schemas import BoundingBox

# Spec: 5% margin; panel snap handles grid sheets so margin stays small on snapped boxes.
MARGIN_RATIO = 0.05
PANEL_SNAP_MARGIN = 0.02
ISOLATED_ASSETS: dict[str, tuple[int, int]] = {
    "symbol_transparent": (1000, 1000),
    "wordmark_transparent": (2000, 500),
    "logo_dark_bg": (1000, 1000),
    "logo_light_bg": (1000, 1000),
}


def hex_to_rgba(hex_color: str, alpha: int = 255) -> tuple[int, int, int, int]:
    cleaned = hex_color.strip().lstrip("#").upper()
    if len(cleaned) == 3:
        cleaned = "".join(ch * 2 for ch in cleaned)
    return (
        int(cleaned[0:2], 16),
        int(cleaned[2:4], 16),
        int(cleaned[4:6], 16),
        alpha,
    )


def sanitize_label(label: str) -> str:
    cleaned = re.sub(r"[^\w\-]+", "_", label.strip().lower())
    return cleaned or "element"


def normalize_bbox(bbox: BoundingBox) -> BoundingBox:
    """Ensure x1<x2, y1<y2 and values stay in 0-1000."""
    x1, x2 = sorted((bbox.x1, bbox.x2))
    y1, y2 = sorted((bbox.y1, bbox.y2))
    return BoundingBox(
        x1=max(0, min(1000, x1)),
        y1=max(0, min(1000, y1)),
        x2=max(0, min(1000, x2)),
        y2=max(0, min(1000, y2)),
    )


def bbox_to_pixel_box(
    bbox: BoundingBox,
    img_width: int,
    img_height: int,
) -> tuple[int, int, int, int]:
    """Convert normalized 0-1000 bbox to pixel coords with margin."""
    normalized = normalize_bbox(bbox)
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


def apply_margin_to_box(
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
