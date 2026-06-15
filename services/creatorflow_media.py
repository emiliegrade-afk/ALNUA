"""CreatorFlow — extract basic media metadata on upload (P1)."""

from __future__ import annotations

import re
import subprocess
import tempfile
from pathlib import Path
from typing import Any

from PIL import Image

_DURATION_RE = re.compile(
    r"Duration:\s*(?:(\d+):(\d+):(\d+(?:\.\d+)?))",
)
_RESOLUTION_RE = re.compile(r"Video:\s.*?(\d{2,5})x(\d{2,5})")


def _ffmpeg_binary() -> str | None:
    try:
        import imageio_ffmpeg

        return imageio_ffmpeg.get_ffmpeg_exe()
    except Exception:
        return None


def _probe_video_ffmpeg(path: str) -> dict[str, Any]:
    ffmpeg = _ffmpeg_binary()
    if not ffmpeg:
        return {}
    try:
        proc = subprocess.run(
            [ffmpeg, "-hide_banner", "-i", path],
            capture_output=True,
            text=True,
            timeout=30,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired):
        return {}

    stderr = proc.stderr or ""
    meta: dict[str, Any] = {}

    duration_match = _DURATION_RE.search(stderr)
    if duration_match:
        hours, minutes, seconds = duration_match.groups()
        total = int(hours) * 3600 + int(minutes) * 60 + float(seconds)
        meta["duration_seconds"] = int(round(total))

    res_match = _RESOLUTION_RE.search(stderr)
    if res_match:
        meta["width"] = int(res_match.group(1))
        meta["height"] = int(res_match.group(2))

    return meta


def _probe_image_pillow(path: str) -> dict[str, Any]:
    try:
        with Image.open(path) as img:
            w, h = img.size
            return {"width": w, "height": h, "format": img.format}
    except Exception:
        return {}


def probe_media_bytes(content: bytes, mime_type: str, *, filename: str = "asset") -> dict[str, Any]:
    """Return duration/resolution metadata without failing the upload pipeline."""
    suffix = Path(filename).suffix or ".bin"
    meta: dict[str, Any] = {"probe_source": "creatorflow_media"}

    tmp_path = Path(tempfile.mkstemp(suffix=suffix)[1])
    try:
        tmp_path.write_bytes(content)
        if mime_type.startswith("video/"):
            meta.update(_probe_video_ffmpeg(str(tmp_path)))
        elif mime_type.startswith("image/"):
            meta.update(_probe_image_pillow(str(tmp_path)))
    finally:
        try:
            tmp_path.unlink(missing_ok=True)
        except PermissionError:
            pass

    return {k: v for k, v in meta.items() if v is not None}
