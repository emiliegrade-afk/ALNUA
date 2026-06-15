"""Google Gemini — text-to-speech via generateContent (REST)."""

from __future__ import annotations

import base64
import io
import struct

import httpx

from config.settings import get_settings

_GEMINI_BASE = "https://generativelanguage.googleapis.com/v1beta"
_DEFAULT_MODEL = "gemini-2.5-flash-preview-tts"
_DEFAULT_VOICE = "Kore"


def _api_key() -> str:
    key = get_settings().studio_google_api_key.strip()
    if not key:
        raise RuntimeError("STUDIO_GOOGLE_API_KEY non configuré")
    return key


def _pcm_to_wav(pcm: bytes, *, rate: int = 24000, channels: int = 1, sample_width: int = 2) -> bytes:
    buf = io.BytesIO()
    buf.write(b"RIFF")
    buf.write(struct.pack("<I", 36 + len(pcm)))
    buf.write(b"WAVE")
    buf.write(b"fmt ")
    buf.write(
        struct.pack(
            "<IHHIIHH",
            16,
            1,
            channels,
            rate,
            rate * channels * sample_width,
            channels * sample_width,
            sample_width * 8,
        )
    )
    buf.write(b"data")
    buf.write(struct.pack("<I", len(pcm)))
    buf.write(pcm)
    return buf.getvalue()


def generate_google_tts(
    text: str,
    *,
    model: str = _DEFAULT_MODEL,
    voice_name: str = _DEFAULT_VOICE,
) -> tuple[bytes, str]:
    """Return (audio_bytes, mime_type)."""
    api_key = _api_key()
    model_id = model if "tts" in model else _DEFAULT_MODEL
    narration = text.strip()
    if not narration:
        raise ValueError("Texte TTS vide")

    payload = {
        "contents": [{"parts": [{"text": narration}]}],
        "generationConfig": {
            "responseModalities": ["AUDIO"],
            "speechConfig": {
                "voiceConfig": {
                    "prebuiltVoiceConfig": {"voiceName": voice_name},
                }
            },
        },
    }

    with httpx.Client(timeout=180.0) as client:
        resp = client.post(
            f"{_GEMINI_BASE}/models/{model_id}:generateContent",
            params={"key": api_key},
            json=payload,
        )
        if resp.status_code >= 400:
            raise RuntimeError(f"Google TTS {resp.status_code}: {resp.text[:400]}")
        data = resp.json()

    try:
        part = data["candidates"][0]["content"]["parts"][0]
        inline = part.get("inlineData") or part.get("inline_data") or {}
        raw_b64 = inline.get("data")
        mime = inline.get("mimeType") or inline.get("mime_type") or "audio/pcm"
    except (KeyError, IndexError) as exc:
        raise RuntimeError("Réponse Google TTS incomplète") from exc

    if not raw_b64:
        raise RuntimeError("Google TTS sans données audio")

    audio = base64.b64decode(raw_b64)
    if mime in ("audio/pcm", "audio/L16", "audio/raw") or not audio.startswith(b"RIFF"):
        return _pcm_to_wav(audio), "audio/wav"
    if mime in ("audio/mpeg", "audio/mp3"):
        return audio, "audio/mpeg"
    if mime == "audio/wav":
        return audio, "audio/wav"
    return _pcm_to_wav(audio), "audio/wav"
