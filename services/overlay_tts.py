"""Overlay TTS — ElevenLabs optional, Edge fallback (Phase 47 Lot 5, DEC-033)."""

from __future__ import annotations

import asyncio
import logging
import re
from typing import Any

logger = logging.getLogger(__name__)

_VOICE_ID_RE = re.compile(r"^[A-Za-z0-9]{10,64}$")
_EL_TIMEOUT_S = 5.0
_EDGE_VOICE = "fr-FR-VivienneMultilingualNeural"
_EDGE_RATE = "-8%"
_EDGE_PITCH = "+2Hz"
_EL_MODEL = "eleven_multilingual_v2"


def _settings() -> Any | None:
    try:
        from config.settings import get_settings

        return get_settings()
    except Exception:
        return None


def elevenlabs_tts_enabled() -> bool:
    s = _settings()
    if s is None:
        return False
    return bool(getattr(s, "elevenlabs_tts", False)) and bool(
        (getattr(s, "elevenlabs_api_key", "") or "").strip()
    )


def voice_id_for(agent_id: str) -> str:
    s = _settings()
    if s is None:
        return ""
    aid = (agent_id or "secretary").strip().lower()
    raw = (
        getattr(s, "elevenlabs_voice_aria", "")
        if aid in {"coo", "aria"}
        else getattr(s, "elevenlabs_voice_nadia", "")
    )
    vid = (raw or "").strip()
    return vid if _VOICE_ID_RE.match(vid) else ""


def _prepare(text: str) -> str:
    import importlib.util
    from pathlib import Path

    path = Path(__file__).resolve().parent.parent / "nadia_desktop" / "core" / "tts_text.py"
    spec = importlib.util.spec_from_file_location("alnua_desk_tts_text", path)
    if spec is None or spec.loader is None:
        return (text or "").strip()[:200]
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return str(mod.prepare_text_for_speech(text, max_chars=200))


def synthesize_elevenlabs(text: str, *, agent_id: str = "secretary") -> bytes:
    """MP3 bytes from ElevenLabs. Empty on skip/failure. Never raises."""
    spoken = (text or "").strip()
    if not spoken or not elevenlabs_tts_enabled():
        return b""
    voice_id = voice_id_for(agent_id)
    if not voice_id:
        return b""
    s = _settings()
    key = (getattr(s, "elevenlabs_api_key", "") or "").strip() if s else ""
    if not key:
        return b""
    try:
        import httpx

        url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
        resp = httpx.post(
            url,
            headers={
                "xi-api-key": key,
                "Accept": "audio/mpeg",
                "Content-Type": "application/json",
            },
            json={
                "text": spoken[:200],
                "model_id": _EL_MODEL,
                "voice_settings": {"stability": 0.45, "similarity_boost": 0.75},
            },
            timeout=_EL_TIMEOUT_S,
        )
        resp.raise_for_status()
        audio = resp.content or b""
        return audio if len(audio) > 64 else b""
    except Exception:
        logger.warning("ElevenLabs TTS failed — will fall back to Edge", exc_info=True)
        return b""


def synthesize_edge(text: str) -> bytes:
    """Edge TTS → MP3 bytes. Empty on failure."""
    spoken = (text or "").strip()
    if not spoken:
        return b""
    try:
        import edge_tts
    except Exception:
        logger.warning("edge-tts absent — TTS désactivé")
        return b""

    async def _run() -> bytes:
        communicate = edge_tts.Communicate(
            spoken, _EDGE_VOICE, rate=_EDGE_RATE, pitch=_EDGE_PITCH
        )
        chunks: list[bytes] = []
        async for chunk in communicate.stream():
            if chunk.get("type") == "audio" and chunk.get("data"):
                chunks.append(chunk["data"])
        return b"".join(chunks)

    try:
        return asyncio.run(_run())
    except RuntimeError:
        try:
            import concurrent.futures

            with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
                return pool.submit(lambda: asyncio.run(_run())).result(timeout=7)
        except Exception:
            logger.warning("edge-tts synthesize failed (nested loop)", exc_info=True)
            return b""
    except Exception:
        logger.warning("edge-tts synthesize failed", exc_info=True)
        return b""


def synthesize_speech(text: str, *, agent_id: str = "secretary") -> bytes:
    """ElevenLabs if configured, else Edge. Never raises."""
    spoken = _prepare(text)
    if not spoken:
        return b""
    audio = synthesize_elevenlabs(spoken, agent_id=agent_id)
    if audio:
        return audio
    return synthesize_edge(spoken)
