"""CreatorFlow media probe tests (P1)."""

from __future__ import annotations

from PIL import Image

from services.creatorflow_media import _probe_image_pillow, probe_media_bytes


def test_probe_image_pillow_extracts_dimensions(tmp_path) -> None:
    path = tmp_path / "sample.png"
    Image.new("RGB", (1280, 720), color=(10, 10, 10)).save(path)
    meta = _probe_image_pillow(str(path))
    assert meta.get("width") == 1280
    assert meta.get("height") == 720


def test_probe_media_bytes_image(tmp_path) -> None:
    path = tmp_path / "sample.png"
    Image.new("RGB", (640, 480)).save(path)
    content = path.read_bytes()
    meta = probe_media_bytes(content, "image/png", filename="sample.png")
    assert meta.get("width") == 640
    assert meta.get("height") == 480
