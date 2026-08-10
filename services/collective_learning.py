"""Collective learning — promote repeated room lessons to L2 (DEC-027)."""

from __future__ import annotations

import hashlib
import json
import logging
import re
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from config.paths import get_hub_repo_path

logger = logging.getLogger(__name__)

_LOCK = threading.Lock()
_CANDIDATES = get_hub_repo_path() / "data" / "lesson_candidates.json"
_COLLECTIVE = get_hub_repo_path() / "data" / "collective_lessons.json"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def promote_min_agents() -> int:
    try:
        from config.settings import get_settings

        return max(2, int(getattr(get_settings(), "collective_promote_min_agents", 3)))
    except Exception:
        return 3


def lesson_fingerprint(lesson: str) -> str:
    norm = " ".join(re.findall(r"[a-z0-9àâäéèêëïîôùûüç]+", (lesson or "").lower()))
    norm = norm[:160]
    return hashlib.sha256(norm.encode("utf-8")).hexdigest()[:16]


def _load(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _save(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


def _room_for(agent_id: str) -> str:
    try:
        from config.agent_personas import get_room

        return get_room(agent_id) or "hub"
    except Exception:
        return "hub"


def record_lesson_candidate(
    agent_id: str,
    lesson: str,
    *,
    task: str = "",
) -> dict[str, Any]:
    """Track lesson; promote to L2 when enough distinct agents in same room."""
    aid = (agent_id or "").strip()
    text = (lesson or "").strip()
    if not aid or not text:
        return {"promoted": False, "reason": "empty"}

    room = _room_for(aid)
    fp = lesson_fingerprint(text)
    key = f"{room}:{fp}"
    thr = promote_min_agents()
    promoted = False
    with _LOCK:
        cand = _load(_CANDIDATES)
        row = cand.get(key) or {
            "room": room,
            "fingerprint": fp,
            "lesson": text[:800],
            "task": (task or "")[:200],
            "agents": [],
            "updated_at": _now(),
        }
        agents = list(row.get("agents") or [])
        if aid not in agents:
            agents.append(aid)
        row["agents"] = agents
        row["lesson"] = text[:800]
        row["updated_at"] = _now()
        cand[key] = row
        _save(_CANDIDATES, cand)

        if len(agents) >= thr and not row.get("promoted"):
            coll = _load(_COLLECTIVE)
            coll[key] = {
                "room": room,
                "fingerprint": fp,
                "lesson": text[:800],
                "agents": agents,
                "promoted_at": _now(),
                "source": "collective_l3_to_l2",
            }
            _save(_COLLECTIVE, coll)
            row["promoted"] = True
            cand[key] = row
            _save(_CANDIDATES, cand)
            promoted = True

    if promoted:
        _write_bureau_mem0(room, text, agents)
        logger.info(
            "collective_learning: promoted room=%s agents=%s fp=%s",
            room,
            agents,
            fp,
        )
    return {
        "promoted": promoted,
        "room": room,
        "fingerprint": fp,
        "agent_count": len(agents) if not promoted else len(agents),
        "threshold": thr,
        "key": key,
    }


def _write_bureau_mem0(room: str, lesson: str, agents: list[str]) -> None:
    try:
        from skills.skill_mem0 import remember

        remember(
            f"[COLLECTIVE L2][{room}] {lesson[:500]} "
            f"(agents: {', '.join(agents[:8])})",
            agent_id=f"bureau:{room}",
        )
    except Exception as exc:
        logger.debug("collective mem0 write skipped: %s", exc)


def list_collective_lessons(*, room: str | None = None, limit: int = 50) -> list[dict[str, Any]]:
    data = _load(_COLLECTIVE)
    rows = list(data.values())
    if room:
        rows = [r for r in rows if r.get("room") == room]
    rows.sort(key=lambda r: str(r.get("promoted_at") or ""), reverse=True)
    return rows[: max(1, min(limit, 200))]


def l2_collective_block(room_id: str | None, *, max_chars: int = 600) -> str:
    rows = list_collective_lessons(room=room_id, limit=3)
    if not rows:
        return ""
    lines = [f"- {r.get('lesson', '')[:180]}" for r in rows]
    block = (
        "\n\n─── L2 COLLECTIVE (leçons bureau) ───\n"
        + "\n".join(lines)
        + "\n─── Fin L2 collective ───"
    )
    return block if len(block) <= max_chars else block[: max_chars - 24] + "\n─── Fin L2 collective ───"
