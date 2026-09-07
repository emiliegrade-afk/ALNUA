"""Telegram Nadia STT/TTS overlay — Lot 1 (mocked IO)."""

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest

from config.settings import get_settings
from services.telegram_voice import (
    build_voice_bytes,
    maybe_send_voice_reply,
    synthesize_speech,
    transcribe_voice_file,
    voice_replies_enabled,
)


@pytest.fixture
def voice_flag(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("TELEGRAM_VOICE_REPLIES", "1")
    get_settings.cache_clear()
    yield
    monkeypatch.setenv("TELEGRAM_VOICE_REPLIES", "0")
    get_settings.cache_clear()


def test_voice_replies_default_off(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("TELEGRAM_VOICE_REPLIES", "0")
    get_settings.cache_clear()
    assert voice_replies_enabled() is False
    get_settings.cache_clear()


def test_voice_replies_on(voice_flag) -> None:
    assert voice_replies_enabled() is True


def test_transcribe_missing_file() -> None:
    assert transcribe_voice_file(Path("/no/such/voice.oga")) == ""


def test_transcribe_without_whisper(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    import sys

    oga = tmp_path / "clip.oga"
    oga.write_bytes(b"ogg")
    monkeypatch.setitem(sys.modules, "faster_whisper", None)
    assert transcribe_voice_file(oga) == ""


def test_synthesize_empty_text() -> None:
    assert synthesize_speech("   ") == b""


def test_synthesize_without_edge_tts(monkeypatch: pytest.MonkeyPatch) -> None:
    import sys

    monkeypatch.setitem(sys.modules, "edge_tts", None)
    assert synthesize_speech("Bonjour Emilie") == b""


def test_build_voice_bytes_skips_when_overlay_none(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "services.voice_overlay.spoken_overlay",
        lambda facts, agent_id="secretary": None,
    )
    assert build_voice_bytes("agenda demain") == b""


def test_build_voice_bytes_uses_tts(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "services.voice_overlay.spoken_overlay",
        lambda facts, agent_id="secretary": "Journée dense.",
    )
    monkeypatch.setattr(
        "services.telegram_voice.synthesize_speech",
        lambda text, agent_id="secretary": b"ID3fake",
    )
    assert build_voice_bytes("12h30 Camille") == b"ID3fake"


@pytest.mark.asyncio
async def test_maybe_send_voice_skips_when_flag_off(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("TELEGRAM_VOICE_REPLIES", "0")
    get_settings.cache_clear()
    update = SimpleNamespace(message=MagicMock())
    await maybe_send_voice_reply(update, "des faits")
    update.message.reply_voice.assert_not_called()
    get_settings.cache_clear()


@pytest.mark.asyncio
async def test_maybe_send_voice_tts_failure_does_not_raise(
    voice_flag, monkeypatch: pytest.MonkeyPatch
) -> None:
    def _boom(facts: str, agent_id: str = "secretary") -> bytes:
        raise RuntimeError("tts")

    monkeypatch.setattr("services.telegram_voice.build_voice_bytes", _boom)
    message = MagicMock()
    message.chat.send_action = AsyncMock()
    message.reply_voice = AsyncMock()
    update = SimpleNamespace(message=message)
    await maybe_send_voice_reply(update, "des faits")
    message.reply_voice.assert_not_called()


@pytest.mark.asyncio
async def test_maybe_send_voice_sends_when_bytes(
    voice_flag, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(
        "services.telegram_voice.build_voice_bytes",
        lambda facts, agent_id="secretary": b"ID3audio",
    )
    message = MagicMock()
    message.chat.send_action = AsyncMock()
    message.reply_voice = AsyncMock()
    update = SimpleNamespace(message=message)
    await maybe_send_voice_reply(update, "des faits")
    message.reply_voice.assert_called_once()


@pytest.mark.asyncio
async def test_send_overlay_voice_via_bot_skips_when_flag_off(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from services.telegram_voice import send_overlay_voice_via_bot

    monkeypatch.setenv("TELEGRAM_VOICE_REPLIES", "0")
    get_settings.cache_clear()
    bot = MagicMock()
    bot.send_voice = AsyncMock()
    await send_overlay_voice_via_bot(bot, 1, "brief")
    bot.send_voice.assert_not_called()
    get_settings.cache_clear()


def test_send_overlay_voice_http_posts_when_on(
    voice_flag, monkeypatch: pytest.MonkeyPatch
) -> None:
    from services.telegram_voice import send_overlay_voice_http

    monkeypatch.setattr(
        "services.telegram_voice.build_voice_bytes",
        lambda facts, agent_id="secretary": b"ID3audio",
    )
    posted = {}

    class _Resp:
        def raise_for_status(self) -> None:
            return None

    class _Client:
        def __init__(self, *a, **k):
            pass

        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

        def post(self, url, data=None, files=None):
            posted["url"] = url
            posted["data"] = data
            posted["files"] = files
            return _Resp()

    monkeypatch.setattr("httpx.Client", _Client)
    monkeypatch.setenv("TELEGRAM_SECRETARY_BOT_TOKEN", "tok")
    monkeypatch.setenv("TELEGRAM_SECRETARY_CHAT_ID", "42")
    get_settings.cache_clear()
    assert send_overlay_voice_http("☀️ Bonjour Emilie") is True
    assert posted["data"]["chat_id"] == "42"
    assert posted["files"]["voice"][0] == "nadia.mp3"
    get_settings.cache_clear()


@pytest.mark.asyncio
async def test_send_morning_brief_sends_overlay(
    voice_flag, monkeypatch: pytest.MonkeyPatch
) -> None:
    from bots.telegram_secretary_handlers import send_morning_brief

    monkeypatch.setattr(
        "bots.telegram_secretary_handlers.morning_message",
        lambda: "☀️ Bonjour Emilie — Nadia ici.\n1. Priorité pipeline",
    )
    overlay = AsyncMock()
    monkeypatch.setattr(
        "services.telegram_voice.send_overlay_voice_via_bot", overlay
    )
    bot = MagicMock()
    bot._chat_id.return_value = 99
    bot.db = MagicMock()
    ctx = SimpleNamespace(bot=MagicMock())
    ctx.bot.send_message = AsyncMock()
    await send_morning_brief(bot, ctx)
    ctx.bot.send_message.assert_awaited()
    overlay.assert_awaited()
    assert overlay.await_args.args[1] == 99


def test_secretary_morning_notify_sends_voice(monkeypatch: pytest.MonkeyPatch) -> None:
    from services.orchestration_morning import run_secretary_morning_notify

    monkeypatch.setattr(
        "services.orchestration_morning.run_morning_orchestration",
        lambda weekly_plan=False, notify=False: {
            "success": True,
            "coo_plan": "p1",
            "briefing_result": {"coo_brief": {"headline": "H"}},
        },
    )
    monkeypatch.setattr(
        "services.secretary_intents.build_combined_morning_message",
        lambda briefing_result=None: "☀️ Bonjour Emilie — Nadia ici.",
    )
    monkeypatch.setattr(
        "services.notify_dedup.should_send_notify",
        lambda *a, **k: True,
    )
    monkeypatch.setattr(
        "skills.skill_telegram_notify.notify_telegram_secretary",
        lambda message, chat_id=None: True,
    )
    monkeypatch.setattr(
        "services.telegram_voice.send_overlay_voice_http",
        lambda facts, chat_id=None: True,
    )
    monkeypatch.setattr("services.orchestration._log_run", lambda *a, **k: None)
    out = run_secretary_morning_notify()
    assert out["notifications"]["telegram"] is True
    assert out["notifications"]["telegram_voice"] is True


@pytest.mark.asyncio
async def test_handle_voice_without_file() -> None:
    from unittest.mock import patch

    from bots.telegram_secretary_voice import handle_voice

    message = MagicMock()
    message.voice = None
    message.reply_text = AsyncMock()
    update = MagicMock()
    update.message = message
    update.effective_chat.id = 1
    bot = MagicMock()

    with (
        patch("bots.telegram_secretary_voice.is_authorized", return_value=True),
        patch(
            "services.rate_limiter.telegram_limiter.is_allowed", return_value=True
        ),
    ):
        await handle_voice(bot, update, MagicMock())
    message.reply_text.assert_awaited()
    assert "Vocal introuvable" in message.reply_text.await_args.args[0]
