"""Google Veo — video generation via Gemini API (REST, no SDK)."""

from __future__ import annotations

import logging
import time

import httpx

from config.settings import get_settings

logger = logging.getLogger(__name__)

_GEMINI_BASE = "https://generativelanguage.googleapis.com/v1beta"
_DEFAULT_MODEL = "veo-3.1-generate-preview"
_POLL_INTERVAL_SEC = 10
_MAX_POLLS = 90  # ~15 min


def _api_key() -> str:
    key = get_settings().studio_google_api_key.strip()
    if not key:
        raise RuntimeError("STUDIO_GOOGLE_API_KEY non configuré")
    return key


def generate_veo_video(
    prompt: str,
    *,
    aspect_ratio: str = "16:9",
    model: str = _DEFAULT_MODEL,
    duration_seconds: int | None = 8,
) -> bytes:
    """Start a long-running Veo job, poll until done, return MP4 bytes."""
    api_key = _api_key()
    model_id = model if model.startswith("veo-") else _DEFAULT_MODEL

    parameters: dict[str, object] = {
        "aspectRatio": aspect_ratio,
        "sampleCount": 1,
    }
    if duration_seconds:
        parameters["durationSeconds"] = duration_seconds

    with httpx.Client(timeout=120.0) as client:
        start = client.post(
            f"{_GEMINI_BASE}/models/{model_id}:predictLongRunning",
            params={"key": api_key},
            json={"instances": [{"prompt": prompt}], "parameters": parameters},
        )
        start.raise_for_status()
        operation_name = start.json().get("name")
        if not operation_name:
            raise RuntimeError("Réponse Veo sans operation name")

        logger.info("Veo operation started: %s", operation_name)

        for attempt in range(_MAX_POLLS):
            if attempt > 0:
                time.sleep(_POLL_INTERVAL_SEC)
            op_resp = client.get(
                f"{_GEMINI_BASE}/{operation_name}",
                params={"key": api_key},
            )
            op_resp.raise_for_status()
            op_data = op_resp.json()

            if not op_data.get("done"):
                continue

            if op_data.get("error"):
                err = op_data["error"]
                raise RuntimeError(err.get("message") or str(err))

            try:
                samples = op_data["response"]["generateVideoResponse"]["generatedSamples"]
                video_uri = samples[0]["video"]["uri"]
            except (KeyError, IndexError) as exc:
                raise RuntimeError("Réponse Veo incomplète") from exc

            video_resp = client.get(video_uri, headers={"x-goog-api-key": api_key}, timeout=300.0)
            video_resp.raise_for_status()
            return video_resp.content

    raise TimeoutError("Délai dépassé — génération Veo non terminée")
