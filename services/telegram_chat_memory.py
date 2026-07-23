"""Short-term chat memory per Telegram chat — conversational continuity."""

from __future__ import annotations

import threading
from collections import deque
from typing import Literal

Role = Literal["user", "assistant"]

_MAX_TURNS = 8
_store: dict[str, deque[tuple[Role, str]]] = {}
_lock = threading.Lock()


def _key(chat_id: int | str | None) -> str:
    return f"tg:{chat_id}" if chat_id is not None else "hub"


def append_turn(chat_id: int | str | None, role: Role, text: str) -> None:
    content = (text or "").strip()
    if not content:
        return
    key = _key(chat_id)
    with _lock:
        if key not in _store:
            _store[key] = deque(maxlen=_MAX_TURNS)
        _store[key].append((role, content[:1200]))


def get_context_block(chat_id: int | str | None, *, max_turns: int = 6) -> str:
    key = _key(chat_id)
    with _lock:
        turns = list(_store.get(key, []))[-max_turns:]
    if not turns:
        return ""
    lines = ["Historique récent de la conversation :"]
    for role, text in turns:
        who = "Emilie" if role == "user" else "Toi"
        lines.append(f"- {who} : {text[:400]}")
    return "\n".join(lines)
