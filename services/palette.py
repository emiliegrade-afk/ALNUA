"""K-means palette extraction and merge with LLM colors."""

from __future__ import annotations

from pathlib import Path

import numpy as np
from PIL import Image
from sklearn.cluster import KMeans

from services.brand_schemas import ColorInfo

KMEANS_THUMB_SIZE = 150
RGB_DEDUP_THRESHOLD = 30


def _hex_to_rgb(hex_color: str) -> tuple[int, int, int]:
    cleaned = hex_color.strip().lstrip("#")
    if len(cleaned) == 3:
        cleaned = "".join(ch * 2 for ch in cleaned)
    return int(cleaned[0:2], 16), int(cleaned[2:4], 16), int(cleaned[4:6], 16)


def _rgb_to_hex(r: int, g: int, b: int) -> str:
    return f"#{r:02X}{g:02X}{b:02X}"


def _rgb_distance(hex_a: str, hex_b: str) -> float:
    r1, g1, b1 = _hex_to_rgb(hex_a)
    r2, g2, b2 = _hex_to_rgb(hex_b)
    return float(np.sqrt((r1 - r2) ** 2 + (g1 - g2) ** 2 + (b1 - b2) ** 2))


def _is_duplicate(hex_color: str, existing: list[ColorInfo]) -> bool:
    return any(_rgb_distance(hex_color, color.hex) < RGB_DEDUP_THRESHOLD for color in existing)


def extract_kmeans_colors(image_path: str, n: int = 5) -> list[ColorInfo]:
    """Extract dominant colors via K-means on a downscaled thumbnail."""
    path = Path(image_path)
    if not path.is_file():
        raise FileNotFoundError(f"Image introuvable: {image_path}")

    with Image.open(path) as img:
        rgb = img.convert("RGB")
        width, height = rgb.size
        if max(width, height) > KMEANS_THUMB_SIZE:
            if width >= height:
                new_w = KMEANS_THUMB_SIZE
                new_h = max(1, int(height * KMEANS_THUMB_SIZE / width))
            else:
                new_h = KMEANS_THUMB_SIZE
                new_w = max(1, int(width * KMEANS_THUMB_SIZE / height))
            rgb = rgb.resize((new_w, new_h), Image.Resampling.BILINEAR)

        pixels = np.asarray(rgb, dtype=np.float32).reshape(-1, 3)
        if pixels.shape[0] < n:
            n = max(1, pixels.shape[0])

        kmeans = KMeans(n_clusters=n, n_init=10, random_state=42)
        labels = kmeans.fit_predict(pixels)
        centers = kmeans.cluster_centers_.astype(int)

        counts = np.bincount(labels, minlength=n)
        ranked = sorted(range(n), key=lambda idx: counts[idx], reverse=True)

        colors: list[ColorInfo] = []
        for rank, idx in enumerate(ranked, start=1):
            r, g, b = centers[idx]
            colors.append(
                ColorInfo(
                    hex=_rgb_to_hex(int(r), int(g), int(b)),
                    name=f"Dominant {rank}",
                    role="secondary",
                    source="kmeans",
                )
            )
        return colors


def merge_palettes(
    llm_colors: list[ColorInfo],
    kmeans_colors: list[ColorInfo],
) -> list[ColorInfo]:
    """Merge palettes — LLM colors keep priority; dedupe K-means by RGB proximity."""
    merged: list[ColorInfo] = list(llm_colors)

    for color in kmeans_colors:
        if not _is_duplicate(color.hex, merged):
            merged.append(color)

    return merged
