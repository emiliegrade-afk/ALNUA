"""L4 Working memory — per-task scratch (DEC-027). Wipe at task end."""

from __future__ import annotations

import json
import logging
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from config.paths import get_hub_repo_path

logger = logging.getLogger(__name__)

_LOCK = threading.Lock()
_DIR = get_hub_repo_path() / "data" / "working_memory"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _safe_id(task_id: str) -> str:
    return "".join(c if c.isalnum() or c in "-_" else "_" for c in (task_id or "x"))[:120]


def _path(task_id: str) -> Path:
    return _DIR / f"{_safe_id(task_id)}.json"


def set_working_memory(
    task_id: str,
    *,
    agent_id: str = "",
    feedback: str = "",
    attempt: int | None = None,
    notes: str = "",
    meta: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Upsert L4 blob for a task (append feedback history)."""
    tid = (task_id or "").strip()
    if not tid:
        return {}
    entry: dict[str, Any] = {
        "task_id": tid,
        "agent_id": (agent_id or "").strip(),
        "updated_at": _now(),
        "attempt": attempt,
        "notes": (notes or "")[:2000],
        "meta": meta or {},
        "feedback_log": [],
    }
    with _LOCK:
        path = _path(tid)
        path.parent.mkdir(parents=True, exist_ok=True)
        if path.exists():
            try:
                prev = json.loads(path.read_text(encoding="utf-8"))
                entry["feedback_log"] = list(prev.get("feedback_log") or [])
                if not entry["agent_id"]:
                    entry["agent_id"] = prev.get("agent_id") or ""
            except Exception:
                pass
        fb = (feedback or "").strip()
        if fb:
            entry["feedback_log"].append({"ts": _now(), "text": fb[:2000]})
            entry["feedback_log"] = entry["feedback_log"][-12:]
        path.write_text(json.dumps(entry, indent=2, ensure_ascii=False), encoding="utf-8")
    return entry


def get_working_memory(task_id: str) -> dict[str, Any] | None:
    tid = (task_id or "").strip()
    if not tid:
        return None
    path = _path(tid)
    if not path.exists():
        return None
    try:
        with _LOCK:
            return json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        logger.debug("working_memory read failed: %s", exc)
        return None


def wipe_working_memory(task_id: str) -> bool:
    """Delete L4 for task — mandatory at task terminal state."""
    tid = (task_id or "").strip()
    if not tid:
        return False
    path = _path(tid)
    with _LOCK:
        if path.exists():
            try:
                path.unlink()
                return True
            except Exception as exc:
                logger.warning("working_memory wipe failed: %s", exc)
                return False
    return False


def sync_loop_l4(
    loop_id: str | None,
    *,
    feedback: str = "",
    attempt: int | None = None,
    agent_id: str = "",
) -> None:
    """Best-effort L4 update from Loop Engine (DEC-027)."""
    if not (loop_id or "").strip():
        return
    try:
        set_working_memory(
            loop_id.strip(),
            agent_id=agent_id,
            feedback=feedback,
            attempt=attempt,
        )
    except Exception:
        pass


def end_loop_l4(loop_id: str | None) -> None:
    """Best-effort wipe L4 when a loop terminates."""
    if not (loop_id or "").strip():
        return
    try:
        wipe_working_memory(loop_id.strip())
    except Exception:
        pass


def l4_block(task_id: str | None, *, loop_feedback: str | None = None, max_chars: int = 1500) -> str:
    parts: list[str] = []
    if loop_feedback and loop_feedback.strip():
        parts.append(f"Feedback loop courant:\n{loop_feedback.strip()[:800]}")
    mem = get_working_memory(task_id) if task_id else None
    if mem:
        hist = mem.get("feedback_log") or []
        if hist:
            lines = [f"- {h.get('text', '')[:200]}" for h in hist[-5:]]
            parts.append("Historique tentatives:\n" + "\n".join(lines))
        if mem.get("notes"):
            parts.append(f"Notes: {mem['notes'][:300]}")
    if not parts:
        return ""
    body = "\n\n".join(parts)
    block = (
        "\n\n─── L4 WORKING (volatile — wipe en fin de task) ───\n"
        f"{body}\n"
        "─── Fin L4 ───"
    )
    return block if len(block) <= max_chars else block[: max_chars - 20] + "\n─── Fin L4 ───"
