"""ElevenLabs — text-to-speech (REST)."""

from __future__ import annotations

import httpx

from config.settings import get_settings

_ELEVEN_BASE = "https://api.elevenlabs.io/v1"
_DEFAULT_MODEL = "eleven_multilingual_v2"


def _api_key() -> str:
    key = get_settings().studio_elevenlabs_api_key.strip()
    if not key:
        raise RuntimeError("STUDIO_ELEVENLABS_API_KEY non configuré")
    return key


def _voice_id(params_voice: str | None) -> str:
    cfg = get_settings()
    return (params_voice or cfg.studio_elevenlabs_voice_id or "EXAVITQu4vr4xnSDxMaL").strip()


def generate_elevenlabs_tts(
    text: str,
    *,
    model: str = _DEFAULT_MODEL,
    voice_id: str | None = None,
    stability: float = 0.5,
    similarity_boost: float = 0.75,
) -> tuple[bytes, str]:
    """Return (mp3_bytes, mime_type)."""
    api_key = _api_key()
    narration = text.strip()
    if not narration:
        raise ValueError("Texte TTS vide")

    vid = _voice_id(voice_id)
    model_id = model or _DEFAULT_MODEL

    with httpx.Client(timeout=180.0) as client:
        resp = client.post(
            f"{_ELEVEN_BASE}/text-to-speech/{vid}",
            headers={
                "xi-api-key": api_key,
                "Content-Type": "application/json",
                "Accept": "audio/mpeg",
            },
            params={"output_format": "mp3_44100_128"},
            json={
                "text": narration,
                "model_id": model_id,
                "voice_settings": {
                    "stability": stability,
                    "similarity_boost": similarity_boost,
                },
            },
        )
        if resp.status_code >= 400:
            raise RuntimeError(f"ElevenLabs TTS {resp.status_code}: {resp.text[:400]}")
        return resp.content, "audio/mpeg"
