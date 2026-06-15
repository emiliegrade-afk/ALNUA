"""OpenRouter — image generation (Flux and compatible models)."""

from __future__ import annotations

import base64
import re

import httpx

from config.settings import get_settings

_OPENROUTER_BASE = "https://openrouter.ai/api/v1"


def generate_openrouter_image(prompt: str, *, model: str) -> bytes:
    """Generate an image via OpenRouter chat completions with image modality."""
    api_key = get_settings().openrouter_api_key.strip()
    if not api_key:
        raise RuntimeError("OPENROUTER_API_KEY non configuré")

    payload = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "modalities": ["image", "text"],
    }

    with httpx.Client(timeout=180.0) as client:
        resp = client.post(
            f"{_OPENROUTER_BASE}/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
                "HTTP-Referer": "https://creatorflow.alnua.app",
                "X-Title": "CreatorFlow Studio",
            },
            json=payload,
        )
        resp.raise_for_status()
        data = resp.json()

    message = data["choices"][0]["message"]
    images = message.get("images") or []
    if images:
        url_or_b64 = images[0].get("image_url", {}).get("url") or images[0].get("url", "")
        return _decode_image_url(url_or_b64)

    # Some models embed base64 in content parts
    content = message.get("content")
    if isinstance(content, list):
        for part in content:
            if part.get("type") == "image_url":
                return _decode_image_url(part["image_url"]["url"])

    raise RuntimeError("OpenRouter n'a pas renvoyé d'image")


def _decode_image_url(url: str) -> bytes:
    if url.startswith("data:"):
        match = re.search(r"base64,(.+)$", url)
        if not match:
            raise RuntimeError("Format data URL image invalide")
        return base64.b64decode(match.group(1))
    with httpx.Client(timeout=120.0) as client:
        r = client.get(url)
        r.raise_for_status()
        return r.content
