"""Aria Telegram STT + overlay only on alert/action/decision (Lot 4)."""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from services.voice_overlay import should_speak_overlay, spoken_overlay


ARIA_ACTION = "Théo bloqué sur le merge Hub. Pipeline Academy : 2 PRs ouvertes."
ARIA_STATUS = "Pipeline Academy : 2 PRs ouvertes."


def test_aria_speaks_action_not_status() -> None:
    assert should_speak_overlay("coo", ARIA_ACTION) is True
    assert should_speak_overlay("aria", ARIA_ACTION) is True
    assert should_speak_overlay("coo", ARIA_STATUS) is False


def test_spoken_overlay_aria_silent_on_status(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("VOICE_OVERLAY_LLM", "0")
    from config.settings import get_settings

    get_settings.cache_clear()
    assert spoken_overlay(ARIA_STATUS, agent_id="coo") is None
    assert spoken_overlay(ARIA_ACTION, agent_id="coo") == "J'agis. Le détail est à l'écran."
    get_settings.cache_clear()


@pytest.mark.asyncio
async def test_handle_voice_without_file() -> None:
    from bots.telegram_coo_voice import handle_voice

    message = MagicMock()
    message.voice = None
    message.reply_text = AsyncMock()
    update = MagicMock()
    update.message = message
    update.effective_chat.id = 1
    bot = MagicMock()

    with (
        patch("bots.telegram_coo_voice.is_authorized", return_value=True),
        patch("services.rate_limiter.telegram_limiter.is_allowed", return_value=True),
    ):
        await handle_voice(bot, update, MagicMock())
    message.reply_text.assert_awaited()
    assert "Vocal introuvable" in message.reply_text.await_args.args[0]


@pytest.mark.asyncio
async def test_reply_aria_sets_coo_voice_agent() -> None:
    from bots.telegram_coo_voice import reply_aria

    update = SimpleNamespace(message=MagicMock(), effective_chat=SimpleNamespace(id=7))
    bot = MagicMock()
    bot._run_coo.return_value = ARIA_ACTION
    captured: dict = {}

    async def _fake_ack(*_a, **kwargs):
        captured.update(kwargs)

    with patch("bots.telegram_delivery.reply_with_ack", _fake_ack):
        await reply_aria(bot, update, "relance Théo")
    assert captured.get("voice_agent_id") == "coo"
    assert captured.get("agent_name") == "Aria"


def test_coo_bot_registers_voice_filter() -> None:
    import inspect

    from bots.telegram_bot_core import TelegramBot

    src = inspect.getsource(TelegramBot.build_application)
    assert "filters.VOICE" in src
    assert "_handle_voice" in src
