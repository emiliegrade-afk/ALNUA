"""
Character-only idle loop with frozen background (Magnific/Kling fallback).

Segments the portrait with rembg, animates only the character layer, composites
back onto the untouched background. Exports a seamless WebM loop.

Usage:
  python scripts/character_static_bg_idle.py --portrait path/to/portrait.png
"""

from __future__ import annotations

import argparse
import math
from pathlib import Path

import cv2
import imageio.v3 as iio
import numpy as np
from PIL import Image
from rembg import remove

ROOT = Path(__file__).resolve().parent.parent


def _ease(t: float) -> float:
    return 0.5 - 0.5 * math.cos(2.0 * math.pi * t)


def _blink_strength(t: float) -> float:
    """Short eyelid closures at 2s and 5s."""
    for center in (2.0, 5.0):
        dt = abs(t - center)
        if dt <= 0.12:
            return 1.0 - (dt / 0.12)
    return 0.0


def _exhale_phase(t: float) -> float:
    """Peaks when chest falls after inhale (breath cycle = 3s)."""
    breath = _ease(t / 3.0)
    return max(0.0, math.sin(2.0 * math.pi * (t / 3.0 - 0.25)) * breath)


def _segment_character(rgb: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    pil = Image.fromarray(rgb)
    rgba = remove(pil).convert("RGBA")
    char = np.array(rgba)
    alpha = char[..., 3].astype(np.float32) / 255.0
    # Feather edges to avoid halo when compositing animated layer.
    alpha = cv2.GaussianBlur(alpha, (0, 0), 1.2)
    return char[..., :3], alpha


def _transform_character(
    char_rgb: np.ndarray,
    alpha: np.ndarray,
    *,
    breath: float,
    tilt_deg: float,
    hand_tension: float,
    hair_shift: float,
    blink: float,
) -> tuple[np.ndarray, np.ndarray]:
    h, w = char_rgb.shape[:2]
    ys, xs = np.where(alpha > 0.08)
    if len(xs) == 0:
        return char_rgb, alpha

    x0, x1 = int(xs.min()), int(xs.max())
    y0, y1 = int(ys.min()), int(ys.max())
    pad = 8
    x0, y0 = max(0, x0 - pad), max(0, y0 - pad)
    x1, y1 = min(w - 1, x1 + pad), min(h - 1, y1 + pad)

    crop_rgb = char_rgb[y0 : y1 + 1, x0 : x1 + 1].copy()
    crop_a = alpha[y0 : y1 + 1, x0 : x1 + 1].copy()

    ch, cw = crop_rgb.shape[:2]
    # Pivot at upper chest — natural for seated-behind-desk pose.
    scale = 1.0 + breath * 0.010
    pivot = (cw / 2, ch * 0.36)
    M = cv2.getRotationMatrix2D(pivot, tilt_deg, scale)
    M[1, 2] += breath * 1.2

    warped_rgb = cv2.warpAffine(
        crop_rgb,
        M,
        (cw, ch),
        flags=cv2.INTER_LANCZOS4,
        borderMode=cv2.BORDER_CONSTANT,
        borderValue=(0, 0, 0),
    )
    warped_a = cv2.warpAffine(
        crop_a,
        M,
        (cw, ch),
        flags=cv2.INTER_LANCZOS4,
        borderMode=cv2.BORDER_CONSTANT,
        borderValue=0,
    )

    out_rgb = char_rgb.copy()
    out_a = alpha.copy()
    out_rgb[y0 : y1 + 1, x0 : x1 + 1] = warped_rgb
    out_a[y0 : y1 + 1, x0 : x1 + 1] = warped_a

    # Hair wisps — horizontal drift on exhale only (upper 35% of character bbox).
    hair_y1 = y0 + int((y1 - y0) * 0.35)
    if hair_shift > 0.01:
        hair_rgb = out_rgb[y0:hair_y1, x0 : x1 + 1].copy()
        hair_a = out_a[y0:hair_y1, x0 : x1 + 1].copy()
        dx = int(hair_shift * 3.5)
        M_h = np.float32([[1, 0, dx], [0, 1, 0]])
        hair_rgb = cv2.warpAffine(
            hair_rgb,
            M_h,
            (hair_rgb.shape[1], hair_rgb.shape[0]),
            flags=cv2.INTER_LINEAR,
            borderMode=cv2.BORDER_REFLECT101,
        )
        hair_a = cv2.warpAffine(
            hair_a,
            M_h,
            (hair_a.shape[1], hair_a.shape[0]),
            flags=cv2.INTER_LINEAR,
            borderMode=cv2.BORDER_REFLECT101,
        )
        out_rgb[y0:hair_y1, x0 : x1 + 1] = hair_rgb
        out_a[y0:hair_y1, x0 : x1 + 1] = hair_a

    # Hand micro-tension — lower-arm bands only, no typing motion.
    if hand_tension > 0.01:
        for band_start, band_end, direction in (
            (0.52, 0.68, 1),
            (0.68, 0.82, -1),
        ):
            by0 = y0 + int((y1 - y0) * band_start)
            by1 = y0 + int((y1 - y0) * band_end)
            patch = out_rgb[by0:by1, x0 : x1 + 1].copy()
            pa = out_a[by0:by1, x0 : x1 + 1].copy()
            dy = int(hand_tension * 1.2 * direction)
            dx = int(hand_tension * 0.6 * direction)
            M_p = np.float32([[1, 0, dx], [0, 1, dy]])
            patch = cv2.warpAffine(
                patch,
                M_p,
                (patch.shape[1], patch.shape[0]),
                flags=cv2.INTER_LINEAR,
                borderMode=cv2.BORDER_REFLECT101,
            )
            pa = cv2.warpAffine(
                pa,
                M_p,
                (pa.shape[1], pa.shape[0]),
                flags=cv2.INTER_LINEAR,
                borderMode=cv2.BORDER_REFLECT101,
            )
            out_rgb[by0:by1, x0 : x1 + 1] = patch
            out_a[by0:by1, x0 : x1 + 1] = pa

    # Blink — darken upper face band briefly.
    if blink > 0.05:
        face_y0 = y0 + int((y1 - y0) * 0.08)
        face_y1 = y0 + int((y1 - y0) * 0.22)
        face_x0 = x0 + int((x1 - x0) * 0.22)
        face_x1 = x0 + int((x1 - x0) * 0.78)
        region = out_rgb[face_y0:face_y1, face_x0:face_x1].astype(np.float32)
        region *= 1.0 - 0.35 * blink
        out_rgb[face_y0:face_y1, face_x0:face_x1] = np.clip(region, 0, 255).astype(
            np.uint8
        )

    # Chest luminance tied to breathing.
    chest_y0 = y0 + int((y1 - y0) * 0.22)
    chest_y1 = y0 + int((y1 - y0) * 0.55)
    chest = out_rgb[chest_y0:chest_y1, x0 : x1 + 1].astype(np.float32)
    chest = np.clip(chest * (1.0 + breath * 0.016), 0, 255).astype(np.uint8)
    out_rgb[chest_y0:chest_y1, x0 : x1 + 1] = chest

    return out_rgb, out_a


def _composite(background: np.ndarray, char_rgb: np.ndarray, alpha: np.ndarray) -> np.ndarray:
    a = alpha[..., None]
    bg = background.astype(np.float32)
    fg = char_rgb.astype(np.float32)
    return np.clip(fg * a + bg * (1.0 - a), 0, 255).astype(np.uint8)


def _render_loop(
    background: np.ndarray,
    char_rgb: np.ndarray,
    alpha: np.ndarray,
    *,
    seconds: float,
    fps: int,
) -> list[np.ndarray]:
    total = max(1, int(round(seconds * fps)))
    frames: list[np.ndarray] = []

    for i in range(total):
        t = i / fps
        breath = _ease(t / 3.0)
        tilt = math.sin(2.0 * math.pi * t / 6.0) * 1.5
        blink = _blink_strength(t)
        hair = _exhale_phase(t) * 0.55
        hand = (math.sin(2.0 * math.pi * t / 4.3) * 0.5 + 0.5) * 0.35

        animated_rgb, animated_a = _transform_character(
            char_rgb,
            alpha,
            breath=breath,
            tilt_deg=tilt,
            hand_tension=hand,
            hair_shift=hair,
            blink=blink,
        )
        frames.append(_composite(background, animated_rgb, animated_a))

    return frames


def _seamless_loop(frames: list[np.ndarray], crossfade: int = 6) -> list[np.ndarray]:
    if len(frames) < 2 or crossfade < 2:
        return frames
    fade = min(crossfade, len(frames) // 4)
    out: list[np.ndarray] = []
    for i, frame in enumerate(frames):
        if i >= len(frames) - fade:
            alpha = (i - (len(frames) - fade)) / max(fade - 1, 1)
            head = frames[i - len(frames) + fade]
            mix = frame.astype(np.float32) * (1.0 - alpha) + head.astype(np.float32) * alpha
            out.append(np.clip(mix, 0, 255).astype(np.uint8))
        else:
            out.append(frame)
    return out


def main() -> None:
    parser = argparse.ArgumentParser(description="Character-only idle loop, static background")
    parser.add_argument("--portrait", type=Path, required=True)
    parser.add_argument("--out", type=Path, default=None)
    parser.add_argument("--seconds", type=float, default=6.0)
    parser.add_argument("--fps", type=int, default=24)
    args = parser.parse_args()

    if not args.portrait.exists():
        raise SystemExit(f"Portrait not found: {args.portrait}")

    rgb = iio.imread(args.portrait)
    if rgb.shape[-1] == 4:
        rgb = rgb[..., :3]

    print("Segmenting character (rembg)…")
    char_rgb, alpha = _segment_character(rgb)
    background = rgb.copy()

    print(f"Rendering {args.seconds}s loop @ {args.fps}fps…")
    frames = _render_loop(background, char_rgb, alpha, seconds=args.seconds, fps=args.fps)
    frames = _seamless_loop(frames)

    stem = args.portrait.stem.replace("-office-9x16", "").replace("-fullbody-desk", "")
    out = args.out or (ROOT / "assets" / "agents" / "animations" / f"{stem}-idle-static-bg.webm")
    out.parent.mkdir(parents=True, exist_ok=True)
    iio.imwrite(out, np.stack(frames), fps=args.fps, codec="libvpx-vp9", quality=10)
    print(f"Saved: {out}")
    print("Note: Magnific + Kling 3.0 unavailable — this is a masked procedural fallback.")


if __name__ == "__main__":
    main()
