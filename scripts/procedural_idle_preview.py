"""
Procedural idle preview from a static portrait (fallback when Runway API unavailable).

Does NOT replace Act-Two — produces a subtle breathing/tilt loop for UI prototyping.

Usage:
  python scripts/procedural_idle_preview.py --portrait assets/agents/aria-voss-coo-portrait-nameplate.png
"""

from __future__ import annotations

import argparse
import math
from pathlib import Path

import cv2
import imageio.v3 as iio
import numpy as np

ROOT = Path(__file__).resolve().parent.parent


def _ease(t: float) -> float:
    return 0.5 - 0.5 * math.cos(2.0 * math.pi * t)


def _transform_frame(
    img: np.ndarray,
    *,
    breath: float,
    tilt_deg: float,
    scan: float,
) -> np.ndarray:
    h, w = img.shape[:2]
    scale = 1.0 + breath * 0.012
    M = cv2.getRotationMatrix2D((w / 2, h * 0.38), tilt_deg, scale)

    # Subtle horizontal parallax for eye-line scan
    M[0, 2] += scan * 3.0
    out = cv2.warpAffine(
        img,
        M,
        (w, h),
        flags=cv2.INTER_LANCZOS4,
        borderMode=cv2.BORDER_REFLECT101,
    )

    # Breathing luminance on skin zone (upper 65%)
    y_cut = int(h * 0.65)
    lum = 1.0 + breath * 0.018
    top = out[:y_cut].astype(np.float32)
    top = np.clip(top * lum, 0, 255).astype(np.uint8)
    out[:y_cut] = top
    return out


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--portrait", type=Path, required=True)
    parser.add_argument("--out", type=Path, default=None)
    parser.add_argument("--seconds", type=float, default=6.0)
    parser.add_argument("--fps", type=int, default=24)
    args = parser.parse_args()

    img = iio.imread(args.portrait)
    if img.shape[-1] == 4:
        img = img[..., :3]

    agent = args.portrait.stem.replace("-portrait-nameplate", "")
    out = args.out or (ROOT / "assets" / "agents" / "animations" / f"{agent}-idle-preview.webm")

    total = max(1, int(round(args.seconds * args.fps)))
    frames: list[np.ndarray] = []

    for i in range(total):
        t = i / args.fps
        breath = _ease(t / 3.0)
        tilt = math.sin(2 * math.pi * t / 6.0) * 1.2
        scan = 0.0
        if 4.0 <= t <= 4.8:
            scan = math.sin(math.pi * (t - 4.0) / 0.8)
        frame = _transform_frame(img, breath=breath, tilt_deg=tilt, scan=scan)
        frames.append(frame)

    out.parent.mkdir(parents=True, exist_ok=True)
    iio.imwrite(out, np.stack(frames), fps=args.fps, codec="libvpx-vp9", quality=8)
    print(f"Preview loop saved: {out}")
    print("For production idle: use scripts/runway_act_two_idle.py with Runway Act-Two.")


if __name__ == "__main__":
    main()
