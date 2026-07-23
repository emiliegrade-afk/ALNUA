"""Telegram chat UX helpers."""

from services.telegram_chat_memory import append_turn, get_context_block
from services.telegram_presence import hub_online


def test_chat_memory_roundtrip() -> None:
    append_turn(999001, "user", "Salut Nadia")
    append_turn(999001, "assistant", "Bonjour Emilie")
    block = get_context_block(999001)
    assert "Salut Nadia" in block
    assert "Bonjour Emilie" in block


def test_hub_online_returns_bool() -> None:
    assert isinstance(hub_online(), bool)
