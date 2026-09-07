"""Lounge tournaments & events calendar (Phase 46 V6)."""

from __future__ import annotations

import json
import threading
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

_PATH = Path(__file__).resolve().parent.parent / "data" / "lounge_tournaments.json"
_lock = threading.Lock()


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _iso(dt: datetime) -> str:
    return dt.isoformat(timespec="seconds")


def _seed_events() -> list[dict[str, Any]]:
    return [
        {
            "id": "code-arena",
            "title": "Tournoi Code Arena",
            "detail": "APP vs R&D — challenges algo",
            "activity": "code_challenge",
            "when_label": "Samedi",
            "starts_at": _iso(_now() + timedelta(days=2)),
            "reward_xp": 200,
            "status": "scheduled",
        },
        {
            "id": "puzzle-master",
            "title": "Puzzle Master",
            "detail": "Challenge quotidien",
            "activity": "puzzle",
            "when_label": "+150 XP",
            "starts_at": _iso(_now()),
            "reward_xp": 150,
            "status": "live",
        },
        {
            "id": "arcade-cup",
            "title": "Arcade Cup",
            "detail": "Course Neon · réflexes",
            "activity": "arcade",
            "when_label": "Dimanche",
            "starts_at": _iso(_now() + timedelta(days=3)),
            "reward_xp": 180,
            "status": "scheduled",
        },
        {
            "id": "strategy-league",
            "title": "Strategy League",
            "detail": "Saison 1 · semaine en cours",
            "activity": "strategy",
            "when_label": "Semaine",
            "starts_at": _iso(_now() - timedelta(days=1)),
            "reward_xp": 120,
            "status": "live",
        },
    ]


def _load() -> dict[str, Any]:
    if not _PATH.exists():
        data = {"events": _seed_events(), "updated_at": _iso(_now())}
        _PATH.parent.mkdir(parents=True, exist_ok=True)
        _PATH.write_text(json.dumps(data, indent=2), encoding="utf-8")
        return data
    data = json.loads(_PATH.read_text(encoding="utf-8"))
    data.setdefault("events", [])
    if not data["events"]:
        data["events"] = _seed_events()
        _PATH.write_text(json.dumps(data, indent=2), encoding="utf-8")
    return data


def list_tournaments() -> list[dict[str, Any]]:
    with _lock:
        data = _load()
        return list(data.get("events") or [])
