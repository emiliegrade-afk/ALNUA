"""Deduplicate identical Hub notifications (Telegram / Discord) within a time window."""

from __future__ import annotations

import hashlib
import time

_DEDUP_SECONDS = 3600
_recent: dict[str, float] = {}


def should_send_notify(channel: str, message: str, *, window_s: int = _DEDUP_SECONDS) -> bool:
    """
    Return False if the same channel+message hash was sent recently.
    Prevents duplicate morning briefings when scheduler + n8n + restarts overlap.
    """
    text = (message or "").strip()
    if not text:
        return False

    digest = hashlib.sha256(text.encode("utf-8")).hexdigest()[:20]
    key = f"{channel}:{digest}"
    now = time.time()

    # Prune stale entries occasionally
    if len(_recent) > 200:
        cutoff = now - window_s
        stale = [k for k, t in _recent.items() if t < cutoff]
        for k in stale:
            _recent.pop(k, None)

    last = _recent.get(key)
    if last is not None and (now - last) < window_s:
        return False

    _recent[key] = now
    return True
