"""Tests for Studio media reference resolution."""

from __future__ import annotations

from unittest.mock import MagicMock

from services.studio.references import resolve_studio_job_params


def test_resolve_reference_asset_id_signs_storage_path() -> None:
    db = MagicMock()
    db.select.return_value = [{"file_url": "user-1/abc_photo.png"}]
    db.raw.storage.from_.return_value.create_signed_url.return_value = {
        "signedURL": "https://signed.test/photo.png",
    }

    out = resolve_studio_job_params(
        {"reference_asset_id": "asset-123", "aspect_ratio": "16:9"},
        "user-1",
        db,
    )

    assert out["prompt_image"] == "https://signed.test/photo.png"
    assert "reference_asset_id" not in out
    assert out["aspect_ratio"] == "16:9"


def test_resolve_prompt_image_storage_path() -> None:
    db = MagicMock()
    db.raw.storage.from_.return_value.create_signed_url.return_value = {
        "signedURL": "https://signed.test/ref.png",
    }

    out = resolve_studio_job_params({"prompt_image": "user-1/ref.png"}, "user-1", db)

    assert out["prompt_image"] == "https://signed.test/ref.png"


def test_resolve_keeps_http_url() -> None:
    db = MagicMock()
    url = "https://cdn.example.com/image.jpg"
    out = resolve_studio_job_params({"prompt_image": url}, "user-1", db)
    assert out["prompt_image"] == url
    db.raw.storage.from_.assert_not_called()


def test_resolve_source_image_path() -> None:
    db = MagicMock()
    out = resolve_studio_job_params({"source_image": "user-1/master.png"}, "user-1", db)
    assert out["source_image"] == "user-1/master.png"
