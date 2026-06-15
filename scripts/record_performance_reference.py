"""
Record a 6-second performance reference for Runway Act-Two (idle or working state).

Usage:
  python scripts/record_performance_reference.py --state working --out assets/agents/aria-voss-working-reference.mp4
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from act_two_states import RECORD_CUES, STATES, get_state

import cv2
import imageio.v3 as iio
import numpy as np


def _draw_hud(
    frame: np.ndarray,
    elapsed: float,
    recording: bool,
    *,
    title: str,
    hint: str,
    cues: list[tuple[float, str]],
) -> np.ndarray:
    out = frame.copy()
    h, w = out.shape[:2]

    status = "REC" if recording else "READY"
    color = (0, 0, 220) if recording else (0, 180, 0)
    cv2.circle(out, (30, 30), 10, color, -1)
    cv2.putText(out, status, (50, 38), cv2.FONT_HERSHEY_SIMPLEX, 0.8, color, 2)

    cv2.putText(
        out,
        f"{elapsed:0.1f}s / {duration:0.1f}s",
        (w - 220, 38),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.8,
        (255, 255, 255),
        2,
    )

    active = cues[0][1]
    for t, text in cues:
        if elapsed >= t:
            active = text

    cv2.rectangle(out, (0, h - 110), (w, h), (0, 0, 0), -1)
    cv2.putText(out, title, (20, h - 82), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (180, 180, 255), 2)
    cv2.putText(out, active, (20, h - 50), cv2.FONT_HERSHEY_SIMPLEX, 0.85, (255, 255, 255), 2)
    cv2.putText(
        out,
        f"Space=start | Q=quit | {hint}",
        (20, h - 15),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.55,
        (200, 200, 200),
        1,
    )
    return out


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--state", choices=list(STATES.keys()), default="working")
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--duration", type=float, default=None)
    parser.add_argument("--fps", type=int, default=24)
    parser.add_argument("--camera", type=int, default=0)
    args = parser.parse_args()

    state = get_state(args.state)
    cues = RECORD_CUES[args.state]
    duration = args.duration if args.duration is not None else state.duration_seconds

    cap = cv2.VideoCapture(args.camera)
    if not cap.isOpened():
        raise SystemExit("Cannot open webcam. Pass --camera N to select another device.")

    args.out.parent.mkdir(parents=True, exist_ok=True)
    frames: list[np.ndarray] = []
    recording = False
    start_time = 0.0

    print(f"State: {args.state}. Waist-up, hands visible at bottom. Press SPACE to start 6s capture.")

    while True:
        ok, frame = cap.read()
        if not ok:
            break

        frame = cv2.flip(frame, 1)
        now = cv2.getTickCount() / cv2.getTickFrequency()
        elapsed = (now - start_time) if recording else 0.0

        if recording:
            frames.append(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
            if elapsed >= duration:
                break

        hud = _draw_hud(
            frame,
            elapsed,
            recording,
            title=state.recorder_title,
            hint=state.recorder_hint,
            cues=cues,
        )
        cv2.imshow(state.recorder_title, hud)

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

    target = int(round(duration * args.fps))
    frames = frames[:target]
    iio.imwrite(args.out, np.stack(frames), fps=args.fps, codec="libx264", quality=8)
    print(f"Saved {args.state} reference: {args.out} ({len(frames)} frames @ {args.fps}fps)")


if __name__ == "__main__":
    main()
