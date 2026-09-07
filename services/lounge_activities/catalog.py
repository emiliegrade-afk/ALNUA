"""Unified Lounge challenge catalog (Phase 46 V6)."""

from __future__ import annotations

from typing import Any

from services.lounge_activities.arcade import CHALLENGES as ARCADE
from services.lounge_activities.code_challenge import CHALLENGES as CODE
from services.lounge_activities.creative import CHALLENGES as CREATIVE
from services.lounge_activities.exploration import CHALLENGES as EXPLORE
from services.lounge_activities.puzzle import (
    PUZZLES,
    evaluate_answer,
    normalize_answer,
)
from services.lounge_activities.simulation import CHALLENGES as SIM
from services.lounge_activities.strategy import CHALLENGES as STRATEGY

ACTIVITY_IDS = (
    "arcade",
    "strategy",
    "puzzle",
    "code_challenge",
    "simulation",
    "exploration",
    "creative",
)


def _puzzle_as_challenges() -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for p in PUZZLES:
        out.append(
            {
                "id": p["id"],
                "activity": "puzzle",
                "title": p["title"],
                "difficulty": p["difficulty"],
                "mode": "exact",
                "prompt": p["prompt"],
                "answer": p["answer"],
                "accepted": list(p.get("accepted", [])),
                "hints": list(p.get("hints", [])),
            }
        )
    return out


_ALL: list[dict[str, Any]] = [
    *ARCADE,
    *STRATEGY,
    *_puzzle_as_challenges(),
    *CODE,
    *SIM,
    *EXPLORE,
    *CREATIVE,
]


def list_activities() -> list[dict[str, Any]]:
    counts = {a: 0 for a in ACTIVITY_IDS}
    for c in _ALL:
        act = str(c.get("activity") or "")
        if act in counts:
            counts[act] += 1
    return [
        {"id": a, "challenge_count": counts[a], "status": "live"}
        for a in ACTIVITY_IDS
    ]


def list_challenges_public(activity: str | None = None) -> list[dict[str, Any]]:
    rows = []
    for c in _ALL:
        if activity and c.get("activity") != activity:
            continue
        rows.append(
            {
                "id": c["id"],
                "activity": c["activity"],
                "title": c["title"],
                "difficulty": c["difficulty"],
                "mode": c.get("mode", "exact"),
                "prompt": c["prompt"],
            }
        )
    return rows


def get_challenge(challenge_id: str) -> dict[str, Any] | None:
    for c in _ALL:
        if c["id"] == challenge_id:
            return c
    return None


def pick_challenge(
    activity: str = "puzzle",
    challenge_id: str | None = None,
) -> dict[str, Any]:
    if challenge_id:
        found = get_challenge(challenge_id)
        if found is None:
            raise ValueError(f"unknown challenge_id: {challenge_id}")
        if activity and found.get("activity") != activity:
            # Allow explicit id even if activity mismatches — prefer id.
            pass
        return found

    pool = [c for c in _ALL if c.get("activity") == activity]
    if not pool:
        raise ValueError(f"unknown activity: {activity}")
    return pool[0]


def evaluate_challenge(challenge: dict[str, Any], raw_answer: str) -> dict[str, Any]:
    mode = str(challenge.get("mode") or "exact")
    if mode == "llm_free":
        norm = (raw_answer or "").strip()
        min_chars = int(challenge.get("min_chars") or 40)
        won = len(norm) >= min_chars
        return {"won": won, "normalized": norm[:500], "expected_hint": None}

    # Reuse puzzle exact matching.
    return evaluate_answer(
        {
            "answer": challenge.get("answer", ""),
            "accepted": challenge.get("accepted", []),
            "hints": challenge.get("hints", []),
        },
        raw_answer,
    )


__all__ = [
    "ACTIVITY_IDS",
    "evaluate_challenge",
    "get_challenge",
    "list_activities",
    "list_challenges_public",
    "normalize_answer",
    "pick_challenge",
]
