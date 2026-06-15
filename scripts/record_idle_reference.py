"""
Record a 6-second idle performance reference for Runway Act-Two.

Sit centered, waist-up, neutral executive office background (or plain wall).
Follow the on-screen timing cues. Keep movements subtle — Act-Two amplifies motion.

Usage:
  python scripts/record_idle_reference.py --out assets/agents/aria-voss-idle-reference.mp4
"""

from __future__ import annotations

import argparse
from pathlib import Path

import cv2
import imageio.v3 as iio
import numpy as np

CUES = [
    (0.0, "Hold still — composed gaze forward"),
    (1.5, "Begin slow inhale (chest rises)"),
    (2.0, "BLINK"),
    (3.0, "Exhale — chest settles"),
    (4.0, "Slow eye scan LEFT → return center"),
    (5.0, "BLINK"),
    (6.0, "Hold — loop end"),
]


def _draw_hud(frame: np.ndarray, elapsed: float, recording: bool) -> np.ndarray:
    out = frame.copy()
    h, w = out.shape[:2]

    status = "REC" if recording else "READY"
    color = (0, 0, 220) if recording else (0, 180, 0)
    cv2.circle(out, (30, 30), 10, color, -1)
    cv2.putText(out, status, (50, 38), cv2.FONT_HERSHEY_SIMPLEX, 0.8, color, 2)

    cv2.putText(
        out,
        f"{elapsed:0.1f}s / 6.0s",
        (w - 220, 38),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.8,
        (255, 255, 255),
        2,
    )

    active = CUES[0][1]
    for t, text in CUES:
        if elapsed >= t:
            active = text

    cv2.rectangle(out, (0, h - 90), (w, h), (0, 0, 0), -1)
    cv2.putText(out, active, (20, h - 50), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (255, 255, 255), 2)
    cv2.putText(
        out,
        "Space=start | Q=quit | Subtle motion only — background frozen",
        (20, h - 15),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.55,
        (200, 200, 200),
        1,
    )
    return out


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--duration", type=float, default=6.0)
    parser.add_argument("--fps", type=int, default=24)
    parser.add_argument("--camera", type=int, default=0)
    args = parser.parse_args()

    cap = cv2.VideoCapture(args.camera)
    if not cap.isOpened():
        raise SystemExit("Cannot open webcam. Pass --camera N to select another device.")

    args.out.parent.mkdir(parents=True, exist_ok=True)
    frames: list[np.ndarray] = []
    recording = False
    start_time = 0.0

    print("Position yourself waist-up, facing camera. Press SPACE to start 6s capture.")

    while True:
        ok, frame = cap.read()
        if not ok:
            break

        frame = cv2.flip(frame, 1)
        now = cv2.getTickCount() / cv2.getTickFrequency()
        elapsed = (now - start_time) if recording else 0.0

        if recording:
            frames.append(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
            if elapsed >= args.duration:
                break

        hud = _draw_hud(frame, elapsed, recording)
        cv2.imshow("ALNUA Idle Reference Recorder", hud)

        key = cv2.waitKey(1) & 0xFF
        if key == ord("q"):
            cap.release()
            cv2.destroyAllWindows()
            return
        if key == ord(" ") and not recording:
            recording = True
            start_time = cv2.getTickCount() / cv2.getTickFrequency()
            frames.clear()

    cap.release()
    cv2.destroyAllWindows()

    if not frames:
        raise SystemExit("No frames captured.")

    target = int(round(args.duration * args.fps))
    frames = frames[:target]
    iio.imwrite(args.out, np.stack(frames), fps=args.fps, codec="libx264", quality=8)
    print(f"Saved reference video: {args.out} ({len(frames)} frames @ {args.fps}fps)")


if __name__ == "__main__":
    main()
