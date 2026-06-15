"""Tests for Studio post-prod providers (upscale, resize export)."""

from __future__ import annotations

from io import BytesIO
from unittest.mock import MagicMock, patch

from PIL import Image

from services.studio.providers.resize_export import _fit_cover, resize_export_bytes
from services.studio.providers.upscale import _scale_factor, upscale_image_bytes
from services.studio.references import resolve_studio_job_params


def test_scale_factor_clamps() -> None:
    assert _scale_factor({}) == 2
    assert _scale_factor({"scale": 3}) == 3
    assert _scale_factor({"scale": 10}) == 4
    assert _scale_factor({"scale": "bad"}) == 2


@patch("services.studio.providers.upscale.load_image_from_params")
def test_upscale_doubles_dimensions(mock_load: MagicMock) -> None:
    mock_load.return_value = Image.new("RGBA", (50, 30), (255, 0, 0, 255))
    db = MagicMock()

    out = upscale_image_bytes({"scale": 2}, "user-1", db)
    result = Image.open(BytesIO(out))

    assert result.size == (100, 60)


def test_fit_cover_crops_to_target() -> None:
    src = Image.new("RGB", (200, 100), (10, 10, 10))
    fitted = _fit_cover(src, 1080, 1920)
    assert fitted.size == (1080, 1920)


@patch("services.studio.providers.resize_export.load_image_from_params")
def test_resize_export_16_9(mock_load: MagicMock) -> None:
    mock_load.return_value = Image.new("RGBA", (800, 800), (0, 255, 0, 255))
    db = MagicMock()

    out = resize_export_bytes({"aspect_ratio": "16:9"}, "user-1", db)
    result = Image.open(BytesIO(out))

    assert result.size == (1920, 1080)


def test_resolve_source_asset_id_keeps_storage_path() -> None:
    db = MagicMock()
    db.select.return_value = [{"file_url": "user-1/source.png"}]

    out = resolve_studio_job_params(
        {"source_asset_id": "asset-99", "aspect_ratio": "9:16"},
        "user-1",
        db,
    )

    assert out["source_image"] == "user-1/source.png"
    assert "source_asset_id" not in out
    assert out["aspect_ratio"] == "9:16"
