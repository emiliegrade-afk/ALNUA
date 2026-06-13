"""
services/competition.py — Gestion des scores de compétition inter-agents ALNUA.

Structure du fichier data/agent_scores.json :
{
  "current_month": "2026-06",
  "scores": {
    "dev_app": 142,
    "dev_backend": 98,
    "qa": 210,
    ...
  },
  "history": {
    "2026-05": { "dev_app": 310, "qa": 450, ... },
    ...
  },
  "milestones_unlocked": {
    "dev_app": ["coffee_break_100", "tier_upgrade_7d_200"],
    ...
  },
  "last_updated": "2026-06-13T14:22:00"
}
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
    "task_completed": 10,
    "task_validated": 25,
    "feature_shipped": 50,
    "bug_found_critical": 30,
    "bug_fixed": 20,
    "review_approved": 15,
    "document_produced": 10,
    "insight_actioned": 35,
}

MILESTONE_THRESHOLDS: list[tuple[int, str, str]] = [
    (100, "coffee_break_100", "coffee_100"),
    (200, "tier_upgrade_7d_200", "tier_7d_200"),
    (500, "tier_upgrade_30d_500", "tier_30d_500"),
]

_SCORES_PATH = Path(__file__).resolve().parent.parent / "data" / "agent_scores.json"
_lock = threading.Lock()


def _empty_data() -> dict[str, Any]:
    now = datetime.now()
    return {
        "current_month": now.strftime("%Y-%m"),
        "scores": {},
        "history": {},
        "milestones_unlocked": {},
        "last_updated": now.isoformat(timespec="seconds"),
    }


def _load_unlocked() -> dict[str, Any]:
    if not _SCORES_PATH.exists():
        data = _empty_data()
        _SCORES_PATH.parent.mkdir(parents=True, exist_ok=True)
        _SCORES_PATH.write_text(json.dumps(data, indent=2), encoding="utf-8")
        return data

    raw = _SCORES_PATH.read_text(encoding="utf-8")
    data = json.loads(raw)
    data.setdefault("current_month", datetime.now().strftime("%Y-%m"))
    data.setdefault("scores", {})
    data.setdefault("history", {})
    data.setdefault("milestones_unlocked", {})
    data.setdefault("last_updated", datetime.now().isoformat(timespec="seconds"))
    return data


def _save_unlocked(data: dict[str, Any]) -> None:
    _SCORES_PATH.parent.mkdir(parents=True, exist_ok=True)
    _SCORES_PATH.write_text(json.dumps(data, indent=2), encoding="utf-8")


def _load() -> dict[str, Any]:
    with _lock:
        return _load_unlocked()


def _save(data: dict[str, Any]) -> None:
    with _lock:
        _save_unlocked(data)


def _resolve_month_scores(data: dict[str, Any], month: str | None) -> dict[str, int]:
    target = month or data["current_month"]
    if target == data["current_month"]:
        return {k: int(v) for k, v in data["scores"].items()}
    history = data["history"].get(target)
    if history is None:
        return {}
    return {k: int(v) for k, v in history.items()}


def _milestone_status(score: int) -> str:
    for threshold, _, status in reversed(MILESTONE_THRESHOLDS):
        if score >= threshold:
            return status
    return "none"


def _unlock_milestones(
    agent_id: str,
    old_score: int,
    new_score: int,
    milestones_unlocked: dict[str, list[str]],
) -> str | None:
    unlocked = milestones_unlocked.setdefault(agent_id, [])
    newly_unlocked: list[str] = []
    for threshold, key, _ in MILESTONE_THRESHOLDS:
        if old_score < threshold <= new_score and key not in unlocked:
            unlocked.append(key)
            newly_unlocked.append(key)
    return newly_unlocked[-1] if newly_unlocked else None


def get_scores(month: str | None = None) -> dict[str, int]:
    """Return scores for the given month (current month by default)."""
    with _lock:
        data = _load_unlocked()
        return _resolve_month_scores(data, month)


def add_points(
    agent_id: str,
    action: str,
    points: int | None = None,
    note: str = "",
) -> dict[str, Any]:
    """Award points to an agent and persist the updated score."""
    agent_id = normalize_agent_id(agent_id)
    points_added = points if points is not None else POINT_VALUES.get(action, 10)

    with _lock:
        data = _load_unlocked()
        old_score = int(data["scores"].get(agent_id, 0))
        new_score = old_score + points_added
        data["scores"][agent_id] = new_score
        milestone_unlocked = _unlock_milestones(
            agent_id,
            old_score,
            new_score,
            data["milestones_unlocked"],
        )
        data["last_updated"] = datetime.now().isoformat(timespec="seconds")
        _save_unlocked(data)

    return {
        "agent_id": agent_id,
        "action": action,
        "points_added": points_added,
        "new_total": new_score,
        "milestone_unlocked": milestone_unlocked,
    }


def get_leaderboard(month: str | None = None) -> list[dict[str, Any]]:
    """Return agents ranked by score (descending), enriched from AGENT_PERSONAS."""
    with _lock:
        data = _load_unlocked()
        scores = _resolve_month_scores(data, month)

    entries: list[dict[str, Any]] = []
    for agent_id, persona in AGENT_PERSONAS.items():
        score = scores.get(agent_id, 0)
        entries.append(
            {
                "agent_id": agent_id,
                "first_name": persona["first_name"],
                "last_name": persona["last_name"],
                "team": persona["team"],
                "score": score,
                "milestone_status": _milestone_status(score),
            }
        )

    entries.sort(key=lambda row: (-row["score"], row["agent_id"]))
    for rank, entry in enumerate(entries, start=1):
        entry["rank"] = rank
    return entries


def get_team_leaderboard(month: str | None = None) -> list[dict[str, Any]]:
    """Aggregate agent scores by team."""
    agent_rows = get_leaderboard(month)
    by_agent = {row["agent_id"]: row for row in agent_rows}

    teams: list[dict[str, Any]] = []
    for team_id, team in TEAMS.items():
        agents = [by_agent[aid] for aid in team.get("agents", []) if aid in by_agent]
        total_score = sum(agent["score"] for agent in agents)
        teams.append(
            {
                "team_id": team_id,
                "team_label": team.get("label", team_id),
                "total_score": total_score,
                "agents": agents,
            }
        )

    teams.sort(key=lambda row: (-row["total_score"], row["team_id"]))
    for rank, team in enumerate(teams, start=1):
        team["rank"] = rank
    return teams


def archive_month(month: str) -> dict[str, Any]:
    """Move month scores into history and reset the current scoreboard."""
    with _lock:
        data = _load_unlocked()
        archived_scores = {k: int(v) for k, v in data["scores"].items()}
        data["history"][month] = archived_scores

        if month == data["current_month"]:
            data["scores"] = {}
            data["milestones_unlocked"] = {}
            data["current_month"] = datetime.now().strftime("%Y-%m")

        data["last_updated"] = datetime.now().isoformat(timespec="seconds")
        _save_unlocked(data)

    return {"archived_month": month, "scores": archived_scores}


def check_and_archive_if_new_month() -> bool:
    """Archive the previous month when the calendar month has changed."""
    with _lock:
        data = _load_unlocked()
        now = datetime.now()
        last_updated = datetime.fromisoformat(data["last_updated"])
        if last_updated.strftime("%Y-%m") == now.strftime("%Y-%m"):
            return False
        month_to_archive = data["current_month"]

    archive_month(month_to_archive)
    return True
