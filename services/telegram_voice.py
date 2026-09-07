"""Telegram STT (Whisper) + Edge TTS bytes — Lot 1 Jarvis overlay (DEC-033)."""

from __future__ import annotations

import asyncio
import importlib.util
import io
import logging
import tempfile
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

OVERLAY_AUDIO_TIMEOUT_S = 12.0
_MAX_VOICE_BYTES = 2_000_000

_whisper_model: Any = None
_tts_text_mod: Any = None


def voice_replies_enabled() -> bool:
    try:
        from config.settings import get_settings

        return bool(get_settings().telegram_voice_replies)
    except Exception:
        return False


def _prepare_for_tts(text: str) -> str:
    global _tts_text_mod
    if _tts_text_mod is None:
        path = Path(__file__).resolve().parent.parent / "nadia_desktop" / "core" / "tts_text.py"
        spec = importlib.util.spec_from_file_location("alnua_desk_tts_text", path)
        if spec is None or spec.loader is None:
            return text.strip()[:200]
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        _tts_text_mod = mod
    return str(_tts_text_mod.prepare_text_for_speech(text, max_chars=200))


def transcribe_voice_file(path: str | Path) -> str:
    """Local faster-whisper STT (French). Empty string on any failure."""
    global _whisper_model
    file_path = Path(path)
    if not file_path.is_file():
        return ""
    try:
        from faster_whisper import WhisperModel
    except Exception:
        logger.warning("faster-whisper absent — STT Telegram désactivé")
        return ""
    try:
        if _whisper_model is None:
            _whisper_model = WhisperModel("base", device="cpu", compute_type="int8")
        segments, _info = _whisper_model.transcribe(
            str(file_path), language="fr", vad_filter=True
        )
        parts = [seg.text.strip() for seg in segments if getattr(seg, "text", "").strip()]
        return " ".join(parts).strip()
    except Exception:
        logger.warning("whisper transcribe failed", exc_info=True)
        return ""


def synthesize_speech(text: str, *, agent_id: str = "secretary") -> bytes:
    """ElevenLabs if enabled, else Edge TTS. Empty bytes on failure."""
    from services.overlay_tts import synthesize_speech as _synth

    return _synth(text, agent_id=agent_id)


def build_voice_bytes(facts: str, *, agent_id: str = "secretary") -> bytes:
    from services.voice_overlay import spoken_overlay

    overlay = spoken_overlay(facts, agent_id=agent_id)
    if not overlay:
        return b""
    return synthesize_speech(overlay, agent_id=agent_id)


async def maybe_send_voice_reply(
    update: Any,
    facts: str,
    *,
    agent_id: str = "secretary",
) -> None:
    """Best-effort audio after the text reply. Never raises to the caller."""
    if not voice_replies_enabled():
        return
    message = getattr(update, "message", None)
    if message is None or not (facts or "").strip():
        return
    try:
        await message.chat.send_action("record_voice")
    except Exception:
        pass
    try:
        audio = await asyncio.wait_for(
            asyncio.to_thread(build_voice_bytes, facts, agent_id=agent_id),
            timeout=OVERLAY_AUDIO_TIMEOUT_S,
        )
    except Exception:
        logger.warning("voice overlay/tts skipped", exc_info=True)
        return
    if not audio:
        return
    try:
        from telegram import InputFile

        await message.reply_voice(
            voice=InputFile(io.BytesIO(audio), filename="nadia.mp3"),
        )
    except Exception:
        logger.warning("telegram send_voice failed", exc_info=True)


def send_overlay_voice_http(facts: str, *, chat_id: int | None = None) -> bool:
    """Sync sendVoice for Hub 8h notify. Never raises. Honors TELEGRAM_VOICE_REPLIES."""
    if not voice_replies_enabled() or not (facts or "").strip():
        return False
    try:
        audio = build_voice_bytes(facts, agent_id="secretary")
    except Exception:
        logger.warning("morning overlay tts skipped", exc_info=True)
        return False
    if not audio:
        return False
    try:
        from config.settings import get_settings

        settings = get_settings()
        token = (
            settings.telegram_secretary_bot_token.strip()
            or settings.telegram_bot_token.strip()
        )
        if not token:
            return False
        target = chat_id
        if target is None:
            raw = settings.telegram_secretary_chat_id_effective
            if not raw:
                return False
            target = int(raw)
        import httpx

        url = f"https://api.telegram.org/bot{token}/sendVoice"
        with httpx.Client(timeout=15.0) as client:
            resp = client.post(
                url,
                data={"chat_id": str(target)},
                files={"voice": ("nadia.mp3", audio, "audio/mpeg")},
            )
            resp.raise_for_status()
        return True
    except Exception:
        logger.warning("morning overlay sendVoice failed", exc_info=True)
        return False


async def send_overlay_voice_via_bot(bot: Any, chat_id: int, facts: str) -> None:
    """Best-effort voice after scheduled text. Never raises."""
    if not voice_replies_enabled() or not (facts or "").strip():
        return
    try:
        audio = await asyncio.wait_for(
            asyncio.to_thread(build_voice_bytes, facts, agent_id="secretary"),
            timeout=OVERLAY_AUDIO_TIMEOUT_S,
        )
    except Exception:
        logger.warning("scheduled overlay tts skipped", exc_info=True)
        return
    if not audio:
        return
    try:
        from telegram import InputFile

        await bot.send_voice(
            chat_id=chat_id,
            voice=InputFile(io.BytesIO(audio), filename="nadia.mp3"),
        )
    except Exception:
        logger.warning("scheduled overlay send_voice failed", exc_info=True)


async def download_telegram_voice(update: Any, context: Any) -> Path | None:
    """Download voice note to a temp file. None if missing/too large."""
    message = getattr(update, "message", None)
    if message is None:
        return None
    voice = getattr(message, "voice", None)
    if voice is None:
        return None
    size = getattr(voice, "file_size", None) or 0
    if size > _MAX_VOICE_BYTES:
        return None
    file_id = getattr(voice, "file_id", None)
    if not file_id:
        return None
    try:
        tg_file = await context.bot.get_file(file_id)
        tmp = tempfile.NamedTemporaryFile(suffix=".oga", delete=False)
        tmp.close()
        dest = Path(tmp.name)
        await tg_file.download_to_drive(custom_path=str(dest))
        return dest
    except Exception:
        logger.warning("telegram voice download failed", exc_info=True)
        return None
