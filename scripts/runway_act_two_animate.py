"""
Runway Act-Two portrait animation pipeline (idle / working / alert states).

Usage:
  set RUNWAYML_API_SECRET=rw_...
  python scripts/runway_act_two_animate.py --state working --agent aria-voss --reference path/to/ref.mp4

Record reference performance:
  python scripts/record_performance_reference.py --state working --out assets/agents/aria-voss-working-reference.mp4
"""

from __future__ import annotations

import argparse
import base64
import mimetypes
import os
import sys
import tempfile
from pathlib import Path

# Allow imports when run as script
sys.path.insert(0, str(Path(__file__).resolve().parent))
from act_two_states import STATES, get_state

import imageio.v3 as iio
import numpy as np

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_PORTRAIT = ROOT / "assets" / "agents" / "aria-voss-coo-portrait-nameplate.png"
DEFAULT_OUT_DIR = ROOT / "assets" / "agents" / "animations"


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
    mime = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
    encoded = base64.b64encode(path.read_bytes()).decode("utf-8")
    return f"data:{mime};base64,{encoded}"


def _run_act_two(
    portrait: Path,
    reference: Path,
    state_name: str,
    *,
    ratio: str = "720:1280",
    seed: int | None = None,
) -> str:
    from runwayml import RunwayML, TaskFailedError

    state = get_state(state_name)
    client = RunwayML(api_key=_require_api_key())

    kwargs: dict = {
        "model": "act_two",
        "character": {"type": "image", "uri": _to_data_uri(portrait)},
        "reference": {"type": "video", "uri": _to_data_uri(reference)},
        "ratio": ratio,
        "body_control": state.body_control,
        "expression_intensity": state.expression_intensity,
    }
    if seed is not None:
        kwargs["seed"] = seed

    print(f"Submitting Act-Two task ({state.name})…")
    print(state.motion_brief)
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
    parser = argparse.ArgumentParser(description="Runway Act-Two agent portrait animation")
    parser.add_argument("--state", choices=list(STATES.keys()), default="working")
    parser.add_argument("--portrait", type=Path, default=DEFAULT_PORTRAIT)
    parser.add_argument("--reference", type=Path, required=True)
    parser.add_argument("--out", type=Path, default=None)
    parser.add_argument("--agent", default="aria-voss")
    parser.add_argument("--ratio", default="720:1280")
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("--skip-act-two", action="store_true")
    parser.add_argument("--input-video", type=Path, default=None)
    args = parser.parse_args()

    if not args.portrait.exists():
        raise SystemExit(f"Portrait not found: {args.portrait}")
    if not args.skip_act_two and not args.reference.exists():
        raise SystemExit(f"Reference video not found: {args.reference}")

    out = args.out or (DEFAULT_OUT_DIR / f"{args.agent}-{args.state}-loop.webm")
    out.parent.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        raw_mp4 = args.input_video or (tmp_path / "act_two_raw.mp4")

        if not args.skip_act_two:
            url = _run_act_two(
                args.portrait,
                args.reference,
                args.state,
                ratio=args.ratio,
                seed=args.seed,
            )
            print(f"Downloading Act-Two output…\n{url}")
            _download(url, raw_mp4)

        state = get_state(args.state)
        _trim_and_loop(raw_mp4, out, target_seconds=state.duration_seconds)
        print(f"Saved {args.state} loop ({state.duration_seconds}s): {out}")


if __name__ == "__main__":
    main()
