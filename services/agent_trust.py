"""Agent Trust System — Phase 31 MVP (DEC-011).

Separate from competition points (cumulative gamification). Trust is a
0–1 score updated from validation outcomes with exponential decay toward
the new sample (not a raw cumulative counter).
"""

from __future__ import annotations

import json
import logging
import threading
from datetime import datetime, timezone
from typing import Any

from config.paths import get_hub_repo_path

logger = logging.getLogger(__name__)

_LOCK = threading.Lock()
_STORE = get_hub_repo_path() / "data" / "agent_trust.json"
_DEFAULT = 0.7
_HISTORY_CAP = 40

# Source-based score caps (DEC-043): paper training must not unlock full
# autonomy on its own. An academy success may lift the score up to this cap;
# going beyond requires production validations (workflow / review board).
ACADEMY_TRUST_CAP = 0.85
_SOURCE_CAPS: tuple[tuple[str, float], ...] = (("academy", ACADEMY_TRUST_CAP),)


def _cap_for(source: str) -> float | None:
    for prefix, cap in _SOURCE_CAPS:
        if source.startswith(prefix):
            return cap
    return None


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _load() -> dict[str, Any]:
    if not _STORE.exists():
        return {"agents": {}}
    try:
        return json.loads(_STORE.read_text(encoding="utf-8"))
    except Exception as exc:
        logger.warning("agent_trust load failed: %s", exc)
        return {"agents": {}}


def _save(data: dict[str, Any]) -> None:
    _STORE.parent.mkdir(parents=True, exist_ok=True)
    _STORE.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


def record_validation(
    agent_id: str,
    *,
    success: bool,
    weight: float = 1.0,
    note: str = "",
    source: str = "workflow",
) -> dict[str, Any]:
    """Update trust for agent_id. success=True raises score, False lowers it."""
    aid = (agent_id or "").strip() or "unknown"
    w = max(0.1, min(float(weight), 3.0))
    sample = 1.0 if success else 0.0
    # Heavier weight → pull harder toward sample (cap 0.45)
    alpha = min(0.45, 0.15 * w)
    cap = _cap_for(source) if success else None

    with _LOCK:
        data = _load()
        agents = data.setdefault("agents", {})
        row = agents.get(aid) or {
            "agent_id": aid,
            "score": _DEFAULT,
            "samples": 0,
            "successes": 0,
            "failures": 0,
            "history": [],
        }
        prev = float(row.get("score", _DEFAULT))
        new_score = round(prev * (1 - alpha) + sample * alpha, 4)
        if cap is not None:
            # A capped source lifts at most to its cap — and never pulls an
            # already-higher score (earned in production) back down.
            new_score = min(new_score, max(prev, cap))
        row["score"] = new_score
        row["samples"] = int(row.get("samples") or 0) + 1
        if success:
            row["successes"] = int(row.get("successes") or 0) + 1
        else:
            row["failures"] = int(row.get("failures") or 0) + 1
        hist = list(row.get("history") or [])
        hist.append(
            {
                "at": _now(),
                "success": success,
                "weight": w,
                "score_after": new_score,
                "note": (note or "")[:120],
                "source": source,
            }
        )
        row["history"] = hist[-_HISTORY_CAP:]
        row["updated_at"] = _now()
        agents[aid] = row
        _save(data)
        return dict(row)


def get_trust(agent_id: str) -> dict[str, Any]:
    aid = (agent_id or "").strip()
    with _LOCK:
        data = _load()
        row = (data.get("agents") or {}).get(aid)
        if not row:
            return {
                "agent_id": aid,
                "score": _DEFAULT,
                "samples": 0,
                "successes": 0,
                "failures": 0,
                "history": [],
                "provisional": True,
            }
        out = dict(row)
        out["provisional"] = False
        return out


def list_trust(*, limit: int = 100) -> list[dict[str, Any]]:
    with _LOCK:
        data = _load()
        rows = list((data.get("agents") or {}).values())
    rows.sort(key=lambda r: float(r.get("score") or 0), reverse=True)
    return rows[: max(1, min(limit, 500))]
