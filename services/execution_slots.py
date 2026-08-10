"""Execution slot scheduler — Phase A isolation (DEC-022).

Bounds concurrency: global / per-repo / per-agent. Acts as a queue when
slots are full (wait_s), then raises SlotBusyError (fail-closed).
"""

from __future__ import annotations

import logging
import threading
import time
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

logger = logging.getLogger(__name__)

_LOCK = threading.RLock()
_SLOTS: dict[str, dict[str, Any]] = {}


class SlotBusyError(RuntimeError):
    """No free execution slot within wait window."""


@dataclass
class SlotLimits:
    max_global: int = 8
    max_per_repo: int = 2
    max_per_agent: int = 1


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def get_limits() -> SlotLimits:
    try:
        from config.settings import get_settings

        s = get_settings()
        return SlotLimits(
            max_global=int(getattr(s, "isolation_max_global", 8)),
            max_per_repo=int(getattr(s, "isolation_max_per_repo", 2)),
            max_per_agent=int(getattr(s, "isolation_max_per_agent", 1)),
        )
    except Exception:
        return SlotLimits()


def _counts() -> tuple[int, dict[str, int], dict[str, int]]:
    by_repo: dict[str, int] = {}
    by_agent: dict[str, int] = {}
    for row in _SLOTS.values():
        repo = str(row.get("repo_key") or "")
        agent = str(row.get("agent_id") or "")
        if repo:
            by_repo[repo] = by_repo.get(repo, 0) + 1
        if agent:
            by_agent[agent] = by_agent.get(agent, 0) + 1
    return len(_SLOTS), by_repo, by_agent


def _can_acquire(agent_id: str, repo_key: str | None, limits: SlotLimits) -> str | None:
    """Return None if OK, else a short reason string."""
    total, by_repo, by_agent = _counts()
    if total >= limits.max_global:
        return f"global_full ({total}/{limits.max_global})"
    if by_agent.get(agent_id, 0) >= limits.max_per_agent:
        return f"agent_full ({agent_id}: {by_agent.get(agent_id, 0)}/{limits.max_per_agent})"
    if repo_key:
        if by_repo.get(repo_key, 0) >= limits.max_per_repo:
            return (
                f"repo_full ({repo_key}: {by_repo.get(repo_key, 0)}/{limits.max_per_repo})"
            )
    return None


def acquire_slot(
    *,
    agent_id: str,
    holder_id: str,
    repo_key: str | None = None,
    wait_s: float = 0.0,
    poll_s: float = 0.25,
    meta: dict[str, Any] | None = None,
) -> str:
    """Acquire a slot; returns slot_token. Raises SlotBusyError if timed out."""
    aid = (agent_id or "").strip()
    hid = (holder_id or "").strip()
    if not aid or not hid:
        raise SlotBusyError("agent_id and holder_id are required")
    repo = (repo_key or "").strip() or None
    limits = get_limits()
    deadline = time.time() + max(0.0, float(wait_s))

    while True:
        with _LOCK:
            reason = _can_acquire(aid, repo, limits)
            if reason is None:
                token = str(uuid.uuid4())[:12]
                _SLOTS[token] = {
                    "token": token,
                    "agent_id": aid,
                    "holder_id": hid,
                    "repo_key": repo,
                    "acquired_at": _now_iso(),
                    "meta": dict(meta or {}),
                }
                logger.info(
                    "execution_slots: acquired token=%s agent=%s repo=%s",
                    token,
                    aid,
                    repo or "-",
                )
                return token

        if time.time() >= deadline:
            raise SlotBusyError(f"Slot busy: {reason}")
        time.sleep(max(0.05, float(poll_s)))


def release_slot(token: str) -> bool:
    tok = (token or "").strip()
    if not tok:
        return False
    with _LOCK:
        row = _SLOTS.pop(tok, None)
        if row:
            logger.info("execution_slots: released token=%s", tok)
            return True
        return False


def release_slots_for_holder(holder_id: str) -> int:
    hid = (holder_id or "").strip()
    if not hid:
        return 0
    with _LOCK:
        tokens = [t for t, r in _SLOTS.items() if r.get("holder_id") == hid]
        for t in tokens:
            del _SLOTS[t]
        return len(tokens)


def list_slots() -> list[dict[str, Any]]:
    with _LOCK:
        return [dict(v) for v in _SLOTS.values()]


def slot_status() -> dict[str, Any]:
    limits = get_limits()
    with _LOCK:
        total, by_repo, by_agent = _counts()
        return {
            "active": total,
            "limits": {
                "max_global": limits.max_global,
                "max_per_repo": limits.max_per_repo,
                "max_per_agent": limits.max_per_agent,
            },
            "by_repo": dict(by_repo),
            "by_agent": dict(by_agent),
            "slots": [dict(v) for v in _SLOTS.values()],
        }


def reset_slots_for_tests() -> None:
    with _LOCK:
        _SLOTS.clear()
