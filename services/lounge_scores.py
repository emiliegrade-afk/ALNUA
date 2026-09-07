"""
services/lounge_scores.py — XP Lounge (DEC-031).

Independent from services/competition.py and agent_trust.
Monthly reset of XP ; lifetime badges kept across months.
"""

from __future__ import annotations

import json
import threading
from datetime import datetime
from pathlib import Path
from typing import Any

from config.agent_models import normalize_agent_id
from config.agent_personas import AGENT_PERSONAS, TEAMS

POINT_VALUES: dict[str, int] = {
    "session_completed": 15,
    "challenge_won": 40,
    "duel_won": 55,
    "collab_completed": 35,
}

# Cosmetic lifetime badges — not reset with the month.
BADGE_THRESHOLDS: list[tuple[int, str]] = [
    (100, "lounge_regular"),
    (300, "challenge_hunter"),
    (600, "lounge_legend"),
]

_SCORES_PATH = Path(__file__).resolve().parent.parent / "data" / "lounge_scores.json"
_lock = threading.Lock()


def _empty_data() -> dict[str, Any]:
    now = datetime.now()
    return {
        "current_month": now.strftime("%Y-%m"),
        "scores": {},
        "history": {},
        "badges_unlocked": {},
        "last_updated": now.isoformat(timespec="seconds"),
    }


def _load_unlocked() -> dict[str, Any]:
    if not _SCORES_PATH.exists():
        data = _empty_data()
        _SCORES_PATH.parent.mkdir(parents=True, exist_ok=True)
        _SCORES_PATH.write_text(json.dumps(data, indent=2), encoding="utf-8")
        return data

    data = json.loads(_SCORES_PATH.read_text(encoding="utf-8"))
    data.setdefault("current_month", datetime.now().strftime("%Y-%m"))
    data.setdefault("scores", {})
    data.setdefault("history", {})
    data.setdefault("badges_unlocked", {})
    data.setdefault("last_updated", datetime.now().isoformat(timespec="seconds"))
    return data


def _save_unlocked(data: dict[str, Any]) -> None:
    _SCORES_PATH.parent.mkdir(parents=True, exist_ok=True)
    _SCORES_PATH.write_text(json.dumps(data, indent=2), encoding="utf-8")


def _resolve_month_scores(data: dict[str, Any], month: str | None) -> dict[str, int]:
    target = month or data["current_month"]
    if target == data["current_month"]:
        return {k: int(v) for k, v in data["scores"].items()}
    history = data["history"].get(target)
    if history is None:
        return {}
    return {k: int(v) for k, v in history.items()}


def _level_for(score: int) -> int:
    # Soft curve: ~100 XP per level floor 1.
    return max(1, score // 100 + 1)


def _unlock_badges(
    agent_id: str,
    old_score: int,
    new_score: int,
    badges_unlocked: dict[str, list[str]],
) -> str | None:
    unlocked = badges_unlocked.setdefault(agent_id, [])
    newly: list[str] = []
    # Lifetime badges use cumulative all-time = history sum + current is heavy;
    # MVP: unlock from current-month totals (still stored for life once earned).
    for threshold, key in BADGE_THRESHOLDS:
        if old_score < threshold <= new_score and key not in unlocked:
            unlocked.append(key)
            newly.append(key)
    return newly[-1] if newly else None


def get_lounge_scores(month: str | None = None) -> dict[str, int]:
    with _lock:
        data = _load_unlocked()
        return _resolve_month_scores(data, month)


def add_lounge_points(
    agent_id: str,
    action: str,
    points: int | None = None,
    note: str = "",
) -> dict[str, Any]:
    agent_id = normalize_agent_id(agent_id)
    points_added = points if points is not None else POINT_VALUES.get(action, 10)

    with _lock:
        data = _load_unlocked()
        old_score = int(data["scores"].get(agent_id, 0))
        new_score = old_score + points_added
        data["scores"][agent_id] = new_score
        badge = _unlock_badges(
            agent_id, old_score, new_score, data["badges_unlocked"]
        )
        data["last_updated"] = datetime.now().isoformat(timespec="seconds")
        _save_unlocked(data)

    return {
        "agent_id": agent_id,
        "action": action,
        "points_added": points_added,
        "new_total": new_score,
        "level": _level_for(new_score),
        "badge_unlocked": badge,
        "note": note[:120] if note else "",
    }


def get_lounge_leaderboard(month: str | None = None) -> list[dict[str, Any]]:
    with _lock:
        data = _load_unlocked()
        scores = _resolve_month_scores(data, month)
        badges = data.get("badges_unlocked", {})

    entries: list[dict[str, Any]] = []
    for agent_id, persona in AGENT_PERSONAS.items():
        score = int(scores.get(agent_id, 0))
        entries.append(
            {
                "agent_id": agent_id,
                "first_name": persona["first_name"],
                "last_name": persona["last_name"],
                "team": persona["team"],
                "score": score,
                "level": _level_for(score),
                "badges": list(badges.get(agent_id, [])),
            }
        )

    entries.sort(key=lambda row: (-row["score"], row["agent_id"]))
    for rank, entry in enumerate(entries, start=1):
        entry["rank"] = rank
    return entries


def get_lounge_team_leaderboard(month: str | None = None) -> list[dict[str, Any]]:
    agent_rows = get_lounge_leaderboard(month)
    by_agent = {row["agent_id"]: row for row in agent_rows}
    teams: list[dict[str, Any]] = []
    for team_id, team in TEAMS.items():
        agents = [by_agent[aid] for aid in team.get("agents", []) if aid in by_agent]
        total = sum(a["score"] for a in agents)
        teams.append(
            {
                "team_id": team_id,
                "team_label": team.get("label", team_id),
                "total_score": total,
                "agents": agents,
            }
        )
    teams.sort(key=lambda row: (-row["total_score"], row["team_id"]))
    for rank, team in enumerate(teams, start=1):
        team["rank"] = rank
    return teams


def get_lounge_profile(agent_id: str) -> dict[str, Any]:
    agent_id = normalize_agent_id(agent_id)
    with _lock:
        data = _load_unlocked()
        score = int(data["scores"].get(agent_id, 0))
        badges = list(data.get("badges_unlocked", {}).get(agent_id, []))
        month = data["current_month"]

    persona = AGENT_PERSONAS.get(agent_id, {})
    return {
        "agent_id": agent_id,
        "first_name": persona.get("first_name", agent_id),
        "last_name": persona.get("last_name", ""),
        "team": persona.get("team", ""),
        "score": score,
        "level": _level_for(score),
        "badges": badges,
        "month": month,
    }


def archive_lounge_month(month: str) -> dict[str, Any]:
    """Archive XP for `month` and reset current board; keep lifetime badges."""
    with _lock:
        data = _load_unlocked()
        archived = {k: int(v) for k, v in data["scores"].items()}
        data["history"][month] = archived
        if month == data["current_month"]:
            data["scores"] = {}
            data["current_month"] = datetime.now().strftime("%Y-%m")
        data["last_updated"] = datetime.now().isoformat(timespec="seconds")
        _save_unlocked(data)
    return {"archived_month": month, "scores": archived}


def check_and_archive_lounge_if_new_month() -> bool:
    with _lock:
        data = _load_unlocked()
        now = datetime.now()
        last_updated = datetime.fromisoformat(data["last_updated"])
        if last_updated.strftime("%Y-%m") == now.strftime("%Y-%m"):
            return False
        month_to_archive = data["current_month"]
    archive_lounge_month(month_to_archive)
    return True
