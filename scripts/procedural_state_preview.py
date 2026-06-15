"""
Procedural state preview from a static portrait (fallback when Runway API unavailable).

Usage:
  python scripts/procedural_state_preview.py --state alert --portrait assets/agents/aria-voss-coo-portrait-nameplate.png
"""

from __future__ import annotations

import argparse
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from act_two_states import STATES, get_state

import cv2
import imageio.v3 as iio
import numpy as np

ROOT = Path(__file__).resolve().parent.parent


def _ease(t: float) -> float:
    return 0.5 - 0.5 * math.cos(2.0 * math.pi * t)


def _activity_factor(t: float, *, pause_at: float = 3.0, pause_dur: float = 0.5) -> float:
    if pause_at <= t < pause_at + pause_dur:
        return 0.08
    return 1.0


def _transform_idle(img: np.ndarray, t: float, _duration: float) -> np.ndarray:
    breath = _ease(t / 3.0)
    tilt = math.sin(2 * math.pi * t / 6.0) * 1.2
    scan = 0.0
    if 4.0 <= t <= 4.8:
        scan = math.sin(math.pi * (t - 4.0) / 0.8)
    return _apply_transform(img, breath=breath, lean_deg=tilt, scan=scan, typing=0.0, frown=0.0)


def _transform_working(img: np.ndarray, t: float, _duration: float) -> np.ndarray:
    act = _activity_factor(t)
    breath = _ease(t / 2.0) * act
    lean = -3.5 * act
    scan = math.sin(2 * math.pi * t / 1.4) * 0.65 * act
    typing = (math.sin(2 * math.pi * t * 5.0) * 0.5 + 0.5) * act
    frown = 0.35 * act if act > 0.5 and (int(t * 2) % 3 == 0) else 0.0
    return _apply_transform(
        img,
        breath=breath,
        lean_deg=lean,
        scan=scan,
        typing=typing,
        frown=frown,
    )


def _transform_alert(img: np.ndarray, t: float, duration: float) -> np.ndarray:
    p = t / duration
    env = math.sin(math.pi * p)

    breath = _ease(p) * 0.25 * (1.0 - 0.6 * env)
    lean = 2.8 * env
    scan = 0.0
    if 0.25 <= p <= 0.85:
        scan = math.sin(math.pi * (p - 0.25) / 0.6) * 0.9

    hand = 0.0
    if 0.35 <= p <= 0.75:
        hand = math.sin(math.pi * (p - 0.35) / 0.4)

    return _apply_transform(
        img,
        breath=breath,
        lean_deg=lean,
        scan=scan,
        typing=0.0,
        frown=0.55 * env,
        hand_raise=hand,
        red_tint=0.18 * env,
        eye_narrow=0.4 * env,
    )


TRANSFORMS = {
    "idle": _transform_idle,
    "working": _transform_working,
    "alert": _transform_alert,
}


def _apply_transform(
    img: np.ndarray,
    *,
    breath: float,
    lean_deg: float,
    scan: float,
    typing: float,
    frown: float,
    hand_raise: float = 0.0,
    red_tint: float = 0.0,
    eye_narrow: float = 0.0,
) -> np.ndarray:
    h, w = img.shape[:2]
    scale = 1.0 + breath * 0.014
    pivot = (w / 2, h * 0.72)
    M = cv2.getRotationMatrix2D(pivot, lean_deg, scale)
    M[0, 2] += scan * 5.0
    M[1, 2] += breath * 2.0

    out = cv2.warpAffine(
        img,
        M,
        (w, h),
        flags=cv2.INTER_LANCZOS4,
        borderMode=cv2.BORDER_REFLECT101,
    )

    y_cut = int(h * 0.72)
    lum = 1.0 + breath * 0.022
    top = out[:y_cut].astype(np.float32)
    top = np.clip(top * lum, 0, 255).astype(np.uint8)
    out[:y_cut] = top

    if frown > 0:
        brow_y0, brow_y1 = int(h * 0.18), int(h * 0.30)
        brow_x0, brow_x1 = int(w * 0.28), int(w * 0.72)
        region = out[brow_y0:brow_y1, brow_x0:brow_x1].astype(np.float32)
        region *= 1.0 - 0.08 * frown
        out[brow_y0:brow_y1, brow_x0:brow_x1] = np.clip(region, 0, 255).astype(np.uint8)

    if eye_narrow > 0:
        eye_y0, eye_y1 = int(h * 0.30), int(h * 0.38)
        eye_x0, eye_x1 = int(w * 0.22), int(w * 0.78)
        region = out[eye_y0:eye_y1, eye_x0:eye_x1].astype(np.float32)
        region *= 1.0 - 0.05 * eye_narrow
        out[eye_y0:eye_y1, eye_x0:eye_x1] = np.clip(region, 0, 255).astype(np.uint8)

    if red_tint > 0:
        face_y0, face_y1 = int(h * 0.12), int(h * 0.62)
        face_x0, face_x1 = int(w * 0.18), int(w * 0.82)
        region = out[face_y0:face_y1, face_x0:face_x1].astype(np.float32)
        region[..., 2] = np.clip(region[..., 2] * (1.0 + 0.12 * red_tint), 0, 255)
        region[..., 1] = np.clip(region[..., 1] * (1.0 - 0.04 * red_tint), 0, 255)
        region[..., 0] = np.clip(region[..., 0] * (1.0 - 0.06 * red_tint), 0, 255)
        out[face_y0:face_y1, face_x0:face_x1] = region.astype(np.uint8)

    if hand_raise > 0:
        side_y0, side_y1 = int(h * 0.42), int(h * 0.72)
        side_x0, side_x1 = int(w * 0.62), int(w * 0.95)
        patch = out[side_y0:side_y1, side_x0:side_x1].copy()
        dy = -int(hand_raise * 14)
        dx = -int(hand_raise * 6)
        M2 = np.float32([[1, 0, dx], [0, 1, dy]])
        warped = cv2.warpAffine(
            patch,
            M2,
            (patch.shape[1], patch.shape[0]),
            flags=cv2.INTER_LINEAR,
            borderMode=cv2.BORDER_REFLECT101,
        )
        out[side_y0:side_y1, side_x0:side_x1] = warped

    if typing > 0:
        strip_y0 = int(h * 0.78)
        strip = out[strip_y0:].copy()
        dx = int(typing * 2.5)
        dy = int(math.sin(typing * math.pi) * 1.5)
        M2 = np.float32([[1, 0, dx], [0, 1, dy]])
        warped = cv2.warpAffine(
            strip,
            M2,
            (strip.shape[1], strip.shape[0]),
            flags=cv2.INTER_LINEAR,
            borderMode=cv2.BORDER_REFLECT101,
        )
        out[strip_y0:] = warped

    return out


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--state", choices=list(STATES.keys()), default="alert")
    parser.add_argument("--portrait", type=Path, required=True)
    parser.add_argument("--out", type=Path, default=None)
    parser.add_argument("--seconds", type=float, default=None)
    parser.add_argument("--fps", type=int, default=24)
    args = parser.parse_args()

    state = get_state(args.state)
    duration = args.seconds if args.seconds is not None else state.duration_seconds

    img = iio.imread(args.portrait)
    if img.shape[-1] == 4:
        img = img[..., :3]

    agent = args.portrait.stem.replace("-portrait-nameplate", "")
    out = args.out or (
        ROOT / "assets" / "agents" / "animations" / f"{agent}-{args.state}-preview.webm"
    )

    total = max(1, int(round(duration * args.fps)))
    transform = TRANSFORMS[args.state]
    frames = [transform(img, i / args.fps, duration) for i in range(total)]

    fade = min(5, total // 4)
    if fade >= 2:
        blended: list[np.ndarray] = []
        for i, frame in enumerate(frames):
            if i >= total - fade:
                alpha = (i - (total - fade)) / max(fade - 1, 1)
                head = frames[i - total + fade]
                mix = frame.astype(np.float32) * (1 - alpha) + head.astype(np.float32) * alpha
                blended.append(np.clip(mix, 0, 255).astype(np.uint8))
            else:
                blended.append(frame)
        frames = blended

    out.parent.mkdir(parents=True, exist_ok=True)
    iio.imwrite(out, np.stack(frames), fps=args.fps, codec="libvpx-vp9", quality=8)
    print(f"{args.state} preview loop saved: {out}")
    print(
        f"For production: python scripts/runway_act_two_animate.py "
        f"--state {args.state} --reference <ref.mp4>"
    )


if __name__ == "__main__":
    main()
