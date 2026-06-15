"""
Runway Act-Two idle loop pipeline for ALNUA agent portraits.

Usage:
  set RUNWAYML_API_SECRET=rw_...
  python scripts/runway_act_two_idle.py --agent aria-voss --reference path/to/idle_ref.mp4

Requires a 3–30s driving performance video (webcam recording recommended).
See scripts/record_idle_reference.py to capture one with on-screen timing cues.
"""

from __future__ import annotations

import argparse
import base64
import mimetypes
import os
import sys
import tempfile
import time
from pathlib import Path

import imageio.v3 as iio
import numpy as np

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_PORTRAIT = ROOT / "assets" / "agents" / "aria-voss-coo-portrait-nameplate.png"
DEFAULT_OUT_DIR = ROOT / "assets" / "agents" / "animations"

MOTION_BRIEF = """
Subtle executive idle loop — zero background movement, only the character lives:
- Breathing cycle: chest rises gently every 3 seconds
- Eye blinks at 2s and 5s
- Very slight ambient hair movement (light air current)
- Micro head tilt 1–2 degrees, slow and imperceptible
- Eyes: slow scan left at 4s, return forward
- Soft subsurface skin light variation with breathing
- Background frozen — no camera drift, no office motion
""".strip()


def _require_api_key() -> str:
    key = (
        os.getenv("RUNWAYML_API_SECRET", "").strip()
        or os.getenv("RUNWAY_API_KEY", "").strip()
        or os.getenv("RUNWAYML_API_KEY", "").strip()
    )
    if not key:
        raise SystemExit(
            "Missing Runway API key. Set RUNWAYML_API_SECRET in .env or environment.\n"
            "Get one at https://dev.runwayml.com/"
        )
    return key


def _to_data_uri(path: Path) -> str:
    mime = mimetypes.guess_type(path.name)[0] or "image/png"
    encoded = base64.b64encode(path.read_bytes()).decode("utf-8")
    return f"data:{mime};base64,{encoded}"


def _run_act_two(
    portrait: Path,
    reference: Path,
    *,
    ratio: str = "720:1280",
    expression_intensity: int = 2,
    body_control: bool = True,
    seed: int | None = None,
) -> str:
    from runwayml import RunwayML, TaskFailedError

    client = RunwayML(api_key=_require_api_key())

    kwargs: dict = {
        "model": "act_two",
        "character": {"type": "image", "uri": _to_data_uri(portrait)},
        "reference": {"type": "video", "uri": _to_data_uri(reference)},
        "ratio": ratio,
        "body_control": body_control,
        "expression_intensity": expression_intensity,
    }
    if seed is not None:
        kwargs["seed"] = seed

    print("Submitting Act-Two task…")
    print(MOTION_BRIEF)
    try:
        task = client.character_performance.create(**kwargs).wait_for_task_output()
    except TaskFailedError as exc:
        raise SystemExit(f"Act-Two failed: {exc.task_details}") from exc

    output = getattr(task, "output", None) or []
    if not output:
        raise SystemExit(f"Act-Two returned no output: {task}")
    return output[0]


def _download(url: str, dest: Path) -> None:
    import httpx

    dest.parent.mkdir(parents=True, exist_ok=True)
    with httpx.Client(timeout=120.0, follow_redirects=True) as client:
        resp = client.get(url)
        resp.raise_for_status()
        dest.write_bytes(resp.content)


def _read_video(path: Path) -> tuple[list[np.ndarray], float]:
    frames = list(iio.imiter(path))
    if not frames:
        raise SystemExit(f"No frames in {path}")
    meta = iio.immeta(path)
    fps = float(meta.get("fps") or 24.0)
    return frames, fps


def _write_webm(frames: list[np.ndarray], dest: Path, fps: float) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    iio.imwrite(
        dest,
        np.stack(frames),
        fps=fps,
        codec="libvpx-vp9",
        quality=10,
        output_params=["-pix_fmt", "yuva420p"],
    )


def _trim_and_loop(
    src: Path,
    dest: Path,
    *,
    target_seconds: float = 6.0,
    crossfade_frames: int = 6,
) -> None:
    frames, fps = _read_video(src)
    target_count = max(1, int(round(target_seconds * fps)))
    frames = frames[:target_count]

    if len(frames) < 2:
        _write_webm(frames, dest, fps)
        return

    # Seamless loop: crossfade tail into head
    fade = min(crossfade_frames, len(frames) // 4)
    if fade >= 2:
        blended: list[np.ndarray] = []
        for i, frame in enumerate(frames):
            if i >= len(frames) - fade:
                t = (i - (len(frames) - fade)) / max(fade - 1, 1)
                head = frames[i - len(frames) + fade] if i - len(frames) + fade >= 0 else frames[0]
                alpha = t
                mix = (
                    frame.astype(np.float32) * (1.0 - alpha)
                    + head.astype(np.float32) * alpha
                )
                blended.append(np.clip(mix, 0, 255).astype(np.uint8))
            else:
                blended.append(frame)
        frames = blended

    _write_webm(frames, dest, fps)


def main() -> None:
    parser = argparse.ArgumentParser(description="Runway Act-Two idle loop for agent portraits")
    parser.add_argument("--portrait", type=Path, default=DEFAULT_PORTRAIT)
    parser.add_argument("--reference", type=Path, required=True, help="3–30s driving performance video")
    parser.add_argument("--out", type=Path, default=None)
    parser.add_argument("--agent", default="aria-voss")
    parser.add_argument("--ratio", default="720:1280")
    parser.add_argument("--expression-intensity", type=int, default=2, choices=range(1, 6))
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("--skip-act-two", action="store_true", help="Only post-process an existing MP4")
    parser.add_argument("--input-video", type=Path, default=None, help="Existing Act-Two output MP4")
    args = parser.parse_args()

    if not args.portrait.exists():
        raise SystemExit(f"Portrait not found: {args.portrait}")
    if not args.skip_act_two and not args.reference.exists():
        raise SystemExit(f"Reference video not found: {args.reference}")

    out = args.out or (DEFAULT_OUT_DIR / f"{args.agent}-idle-loop.webm")
    out.parent.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        raw_mp4 = args.input_video or (tmp_path / "act_two_raw.mp4")

        if not args.skip_act_two:
            url = _run_act_two(
                args.portrait,
                args.reference,
                ratio=args.ratio,
                expression_intensity=args.expression_intensity,
                seed=args.seed,
            )
            print(f"Downloading Act-Two output…\n{url}")
            _download(url, raw_mp4)

        _trim_and_loop(raw_mp4, out)
        print(f"Saved idle loop: {out}")


if __name__ == "__main__":
    main()
