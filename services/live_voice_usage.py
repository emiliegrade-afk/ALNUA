"""Nadia Live — daily voice minutes (SPEC_JARVIS_LIVE §7, DEC-038).

The cap exists to bound an open microphone's cost. The Hub cannot see the WebRTC
audio (it goes browser -> OpenAI), so duration is measured from the moment the Hub
minted the secret. The browser reports the end of a session; it can never claim more
than the wall clock allows. A session that was never reported (crash, closed tab) is
settled at the next mint with a fixed, conservative charge instead of being free.

Runtime state ``data/live_voice_usage.json`` is git-ignored.
"""

from __future__ import annotations

import json
import threading
import time
import uuid
from datetime import date
from pathlib import Path
from typing import Any

# Charged when a session was opened but its end was never reported.
UNREPORTED_CHARGE_SECONDS = 300
# Tolerance between the browser's clock and the Hub's when validating a report.
REPORT_SLACK_SECONDS = 5
KEEP_DAYS = 14

_lock = threading.RLock()
_path_override: Path | None = None


def _path() -> Path:
    if _path_override is not None:
        return _path_override
    from config.paths import get_hub_repo_path

    return get_hub_repo_path() / "data" / "live_voice_usage.json"


def _load() -> dict[str, Any]:
    try:
        data = json.loads(_path().read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {"days": {}, "open": {}}
    if not isinstance(data, dict):
        return {"days": {}, "open": {}}
    data.setdefault("days", {})
    data.setdefault("open", {})
    return data


def _save(data: dict[str, Any]) -> None:
    days = sorted(data["days"])[-KEEP_DAYS:]
    data["days"] = {d: data["days"][d] for d in days}
    path = _path()
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(data, indent=2), encoding="utf-8")
    tmp.replace(path)


def _today() -> str:
    return date.today().isoformat()


def _add(data: dict[str, Any], seconds: float) -> None:
    day = _today()
    data["days"][day] = round(float(data["days"].get(day, 0)) + max(0.0, seconds), 1)


def _settle_unreported(data: dict[str, Any], now: float) -> None:
    for started in data["open"].values():
        _add(data, min(max(0.0, now - float(started)), UNREPORTED_CHARGE_SECONDS))
    data["open"] = {}


def used_seconds() -> float:
    with _lock:
        return float(_load()["days"].get(_today(), 0))


def remaining_seconds(max_minutes: int) -> int:
    return max(0, int(max_minutes * 60 - used_seconds()))


def open_session(now: float | None = None) -> str:
    """Register a minted session and return its id. Settles any forgotten one first."""
    now = time.time() if now is None else now
    with _lock:
        data = _load()
        _settle_unreported(data, now)
        session_id = uuid.uuid4().hex
        data["open"][session_id] = now
        _save(data)
        return session_id


def close_session(session_id: str, seconds: float, now: float | None = None) -> bool:
    """Record a reported duration, capped by the real elapsed time. False if unknown."""
    now = time.time() if now is None else now
    with _lock:
        data = _load()
        started = data["open"].pop(session_id, None)
        if started is None:
            return False
        elapsed = max(0.0, now - float(started)) + REPORT_SLACK_SECONDS
        _add(data, min(max(0.0, seconds), elapsed))
        _save(data)
        return True


def reset_for_tests(path: Path | None) -> None:
    global _path_override
    _path_override = path
