"""Runway Gen-4 — text/image-to-video via official REST API (httpx)."""

from __future__ import annotations

import logging
import os
import time

import httpx

from config.settings import get_settings

logger = logging.getLogger(__name__)

_RUNWAY_BASE = "https://api.dev.runwayml.com/v1"
_RUNWAY_VERSION = "2024-11-06"
_DEFAULT_MODEL = "gen4_turbo"
_POLL_INTERVAL_SEC = 5
_MAX_POLLS = 120  # ~10 min

_ASPECT_TO_RATIO: dict[str, str] = {
    "16:9": "1280:720",
    "9:16": "720:1280",
    "1:1": "960:960",
    "4:3": "1104:832",
    "3:4": "832:1104",
    "4:5": "832:1104",
    "21:9": "1584:672",
}

_MODEL_ALIASES: dict[str, str] = {
    "gen-4": "gen4_turbo",
    "gen4": "gen4_turbo",
    "gen4-turbo": "gen4_turbo",
    "gen4_turbo": "gen4_turbo",
    "gen4.5": "gen4.5",
    "gen45": "gen4.5",
}


def _api_key() -> str:
    cfg = get_settings()
    key = cfg.studio_runway_api_key.strip() or os.getenv("RUNWAYML_API_SECRET", "").strip()
    if not key:
        raise RuntimeError("STUDIO_RUNWAY_API_KEY ou RUNWAYML_API_SECRET non configuré")
    return key


def _headers(api_key: str) -> dict[str, str]:
    return {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "X-Runway-Version": _RUNWAY_VERSION,
    }


def _normalize_model(model: str) -> str:
    raw = (model or _DEFAULT_MODEL).strip().lower()
    return _MODEL_ALIASES.get(raw, raw or _DEFAULT_MODEL)


def _ratio(aspect_ratio: str) -> str:
    if ":" in aspect_ratio and aspect_ratio.count(":") == 1:
        left, right = aspect_ratio.split(":", 1)
        if left.isdigit() and right.isdigit():
            return aspect_ratio
    return _ASPECT_TO_RATIO.get(aspect_ratio, "1280:720")


def _duration_seconds(params_duration: object) -> int:
    try:
        value = int(params_duration)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return 5
    return 10 if value >= 10 else 5


def generate_runway_video(
    prompt: str,
    *,
    model: str = _DEFAULT_MODEL,
    aspect_ratio: str = "16:9",
    duration: int = 5,
    prompt_image: str | None = None,
) -> bytes:
    """Text-to-video (or image-to-video if prompt_image URL/data-uri is set)."""
    api_key = _api_key()
    model_id = _normalize_model(model)
    body: dict[str, object] = {
        "promptText": prompt,
        "model": model_id,
        "ratio": _ratio(aspect_ratio),
        "duration": _duration_seconds(duration),
    }
    if prompt_image:
        body["promptImage"] = prompt_image

    with httpx.Client(timeout=120.0) as client:
        start = client.post(
            f"{_RUNWAY_BASE}/image_to_video",
            headers=_headers(api_key),
            json=body,
        )
        if start.status_code >= 400:
            detail = start.text[:400]
            raise RuntimeError(f"Runway API {start.status_code}: {detail}")

        task_id = start.json().get("id")
        if not task_id:
            raise RuntimeError("Réponse Runway sans task id")

        logger.info("Runway task started: %s (model=%s)", task_id, model_id)

        for _ in range(_MAX_POLLS):
            time.sleep(_POLL_INTERVAL_SEC)
            poll = client.get(
                f"{_RUNWAY_BASE}/tasks/{task_id}",
                headers=_headers(api_key),
            )
            poll.raise_for_status()
            data = poll.json()
            status = str(data.get("status", "")).upper()

            if status in ("PENDING", "RUNNING", "THROTTLED"):
                continue
            if status == "FAILED":
                err = data.get("failure") or data.get("failureCode") or data.get("error")
                raise RuntimeError(f"Runway task failed: {err or status}")
            if status != "SUCCEEDED":
                raise RuntimeError(f"Runway statut inattendu: {status}")

            output = data.get("output") or []
            if not output:
                raise RuntimeError("Runway task succeeded but output is empty")

            video_url = output[0] if isinstance(output[0], str) else output[0].get("url")
            if not video_url:
                raise RuntimeError("Runway output sans URL vidéo")

            video_resp = client.get(video_url, timeout=300.0, follow_redirects=True)
            video_resp.raise_for_status()
            return video_resp.content

    raise TimeoutError("Délai dépassé — génération Runway non terminée")
