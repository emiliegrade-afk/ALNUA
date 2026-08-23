"""
Lounge session runtime — multi-activity (DEC-031 / Phase 46 V3–V6).

Persists to data/lounge_sessions.json. Never writes production repos/secrets.
"""

from __future__ import annotations

import json
import threading
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from config.agent_models import normalize_agent_id
from services.lounge_activities.catalog import (
    ACTIVITY_IDS,
    evaluate_challenge,
    list_activities,
    list_challenges_public,
    pick_challenge,
)
from services.lounge_scores import add_lounge_points, check_and_archive_lounge_if_new_month

_SESSIONS_PATH = Path(__file__).resolve().parent.parent / "data" / "lounge_sessions.json"
_lock = threading.Lock()
_MAX_SESSIONS = 200


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _empty() -> dict[str, Any]:
    return {"sessions": [], "updated_at": _now()}


def _load_unlocked() -> dict[str, Any]:
    if not _SESSIONS_PATH.exists():
        data = _empty()
        _SESSIONS_PATH.parent.mkdir(parents=True, exist_ok=True)
        _SESSIONS_PATH.write_text(json.dumps(data, indent=2), encoding="utf-8")
        return data
    data = json.loads(_SESSIONS_PATH.read_text(encoding="utf-8"))
    data.setdefault("sessions", [])
    return data


def _save_unlocked(data: dict[str, Any]) -> None:
    data["updated_at"] = _now()
    sessions = data.get("sessions", [])
    if len(sessions) > _MAX_SESSIONS:
        data["sessions"] = sessions[-_MAX_SESSIONS:]
    _SESSIONS_PATH.parent.mkdir(parents=True, exist_ok=True)
    _SESSIONS_PATH.write_text(json.dumps(data, indent=2), encoding="utf-8")


def _public_session(session: dict[str, Any], *, reveal: bool = False) -> dict[str, Any]:
    out = {
        "id": session["id"],
        "agent_id": session["agent_id"],
        "activity": session["activity"],
        "status": session["status"],
        "challenge_id": session.get("challenge_id") or session.get("puzzle_id"),
        "puzzle_id": session.get("puzzle_id") or session.get("challenge_id"),
        "puzzle_title": session.get("puzzle_title"),
        "puzzle_prompt": session.get("puzzle_prompt"),
        "difficulty": session.get("difficulty"),
        "mode": session.get("mode", "exact"),
        "started_at": session.get("started_at"),
        "completed_at": session.get("completed_at"),
        "won": session.get("won"),
        "agent_answer": session.get("agent_answer"),
        "points_awarded": session.get("points_awarded"),
        "score_action": session.get("score_action"),
    }
    if reveal or session.get("status") == "completed":
        out["correct_answer"] = session.get("correct_answer")
    return out


def list_puzzles() -> list[dict[str, Any]]:
    return list_challenges_public("puzzle")


def list_lounge_activities() -> list[dict[str, Any]]:
    return list_activities()


def list_lounge_challenges(activity: str | None = None) -> list[dict[str, Any]]:
    return list_challenges_public(activity)


def list_active_sessions() -> list[dict[str, Any]]:
    with _lock:
        data = _load_unlocked()
        active = [s for s in data["sessions"] if s.get("status") == "active"]
    return [_public_session(s) for s in active]


def list_recent_sessions(limit: int = 20) -> list[dict[str, Any]]:
    with _lock:
        data = _load_unlocked()
        sessions = list(reversed(data["sessions"]))[:limit]
    return [_public_session(s) for s in sessions]


def get_session(session_id: str) -> dict[str, Any] | None:
    with _lock:
        data = _load_unlocked()
        for s in data["sessions"]:
            if s["id"] == session_id:
                return _public_session(s)
    return None


def start_session(
    agent_id: str,
    activity: str = "puzzle",
    challenge_id: str | None = None,
) -> dict[str, Any]:
    agent_id = normalize_agent_id(agent_id)
    activity = (activity or "puzzle").strip()
    if activity not in ACTIVITY_IDS:
        raise ValueError(f"unknown activity: {activity}")

    challenge = pick_challenge(activity, challenge_id)

    if challenge_id is None:
        with _lock:
            data = _load_unlocked()
            used = {
                s.get("challenge_id") or s.get("puzzle_id")
                for s in data["sessions"][-40:]
                if s.get("agent_id") == agent_id and s.get("activity") == activity
            }
        pool = list_challenges_public(activity)
        for row in pool:
            if row["id"] not in used:
                challenge = pick_challenge(activity, row["id"])
                break

    session = {
        "id": str(uuid.uuid4()),
        "agent_id": agent_id,
        "activity": activity,
        "status": "active",
        "challenge_id": challenge["id"],
        "puzzle_id": challenge["id"],
        "puzzle_title": challenge["title"],
        "puzzle_prompt": challenge["prompt"],
        "difficulty": challenge.get("difficulty"),
        "mode": challenge.get("mode", "exact"),
        "correct_answer": challenge.get("answer"),
        "accepted": list(challenge.get("accepted", [])),
        "min_chars": challenge.get("min_chars"),
        "started_at": _now(),
        "completed_at": None,
        "won": None,
        "agent_answer": None,
        "points_awarded": None,
        "score_action": None,
    }

    with _lock:
        data = _load_unlocked()
        data["sessions"].append(session)
        _save_unlocked(data)

    return _public_session(session)


def start_puzzle_session(
    agent_id: str,
    puzzle_id: str | None = None,
) -> dict[str, Any]:
    return start_session(agent_id, activity="puzzle", challenge_id=puzzle_id)


def complete_session(session_id: str, raw_answer: str) -> dict[str, Any]:
    from services.input_sanitizer import sanitize_user_input

    clean = sanitize_user_input(raw_answer or "", max_length=2000, redact_pii_enabled=False)
    check_and_archive_lounge_if_new_month()

    with _lock:
        data = _load_unlocked()
        session = next((s for s in data["sessions"] if s["id"] == session_id), None)
        if session is None:
            raise KeyError(f"session not found: {session_id}")
        if session.get("status") != "active":
            return _public_session(session, reveal=True)

        challenge = {
            "mode": session.get("mode", "exact"),
            "answer": session.get("correct_answer"),
            "accepted": session.get("accepted", []),
            "hints": [],
            "min_chars": session.get("min_chars") or 40,
        }
        result = evaluate_challenge(challenge, clean)
        session["agent_answer"] = clean
        session["won"] = result["won"]
        session["status"] = "completed"
        session["completed_at"] = _now()
        agent_id = session["agent_id"]
        _save_unlocked(data)

    action = "challenge_won" if result["won"] else "session_completed"
    scored = add_lounge_points(
        agent_id,
        action,
        note=f"{session.get('activity')}:{session.get('challenge_id')}",
    )
    with _lock:
        data = _load_unlocked()
        for s in data["sessions"]:
            if s["id"] == session_id:
                s["points_awarded"] = scored["points_added"]
                s["score_action"] = action
                session = s
                break
        _save_unlocked(data)

    return _public_session(session, reveal=True)


def complete_puzzle_session(session_id: str, raw_answer: str) -> dict[str, Any]:
    return complete_session(session_id, raw_answer)


def run_session_with_llm(session_id: str) -> dict[str, Any]:
    from agents.base import LLMClient, parse_json_response
    from services.input_sanitizer import sanitize_user_input
    from services.lounge_llm import get_lounge_model

    with _lock:
        data = _load_unlocked()
        session = next((s for s in data["sessions"] if s["id"] == session_id), None)
        if session is None:
            raise KeyError(f"session not found: {session_id}")
        if session.get("status") != "active":
            return _public_session(session, reveal=True)
        prompt = session["puzzle_prompt"]
        agent_id = session["agent_id"]
        title = session.get("puzzle_title", "Challenge")
        mode = session.get("mode", "exact")

    system = (
        "Tu es un agent ALNUA en session Agent Lounge (isolée). "
        "Réponds UNIQUEMENT en JSON : "
        '{"answer":"...","reasoning":"..."}. Pas d\'autre texte.'
    )
    user = sanitize_user_input(
        f"Challenge « {title} » ({mode}) :\n{prompt}",
        max_length=2000,
        redact_pii_enabled=False,
    )

    raw = LLMClient().complete(
        system=system,
        user=user,
        model=get_lounge_model(),
        agent_id=agent_id,
        method_name="lounge_challenge",
        temperature=0.3 if mode == "llm_free" else 0.2,
        max_tokens=600 if mode == "llm_free" else 400,
    )
    parsed = parse_json_response(raw)
    answer = ""
    if isinstance(parsed, dict):
        answer = str(parsed.get("answer") or "")
    if not answer:
        answer = (raw or "").strip()[:1500]

    return complete_session(session_id, answer)


def run_puzzle_with_llm(session_id: str) -> dict[str, Any]:
    return run_session_with_llm(session_id)
