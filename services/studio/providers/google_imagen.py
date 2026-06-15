"""Google Imagen — image generation via Gemini API (REST)."""

from __future__ import annotations

import base64

import httpx

from config.settings import get_settings

_GEMINI_BASE = "https://generativelanguage.googleapis.com/v1beta"
_DEFAULT_MODEL = "imagen-3.0-generate-002"


def _api_key() -> str:
    key = get_settings().studio_google_api_key.strip()
    if not key:
        raise RuntimeError("STUDIO_GOOGLE_API_KEY non configuré")
    return key


def generate_imagen_image(
    prompt: str,
    *,
    model: str = _DEFAULT_MODEL,
    aspect_ratio: str = "1:1",
) -> bytes:
    api_key = _api_key()
    model_id = model if model.startswith("imagen-") else _DEFAULT_MODEL

    with httpx.Client(timeout=120.0) as client:
        resp = client.post(
            f"{_GEMINI_BASE}/models/{model_id}:predict",
            params={"key": api_key},
            json={
                "instances": [{"prompt": prompt}],
                "parameters": {
                    "sampleCount": 1,
                    "aspectRatio": aspect_ratio,
                },
            },
        )
        resp.raise_for_status()
        data = resp.json()

    predictions = data.get("predictions") or data.get("generatedImages") or []
    if not predictions:
        raise RuntimeError("Réponse Imagen sans image")

    first = predictions[0]
    b64 = first.get("bytesBase64Encoded") or first.get("image", {}).get("bytesBase64Encoded")
    if not b64:
        raise RuntimeError("Format Imagen inattendu")
    return base64.b64decode(b64)
