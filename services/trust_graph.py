"""Trust Graph — append-only allow/deny journal (DEC-026)."""

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
_STORE = get_hub_repo_path() / "data" / "trust_graph.jsonl"
_MAX_READ = 500


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _path() -> Path:
    return _STORE


def record_decision(
    *,
    agent_id: str,
    capability: str,
    allowed: bool,
    reason: str,
    resource: str | None = None,
    meta: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Append one Trust Graph decision (never raises to caller for I/O)."""
    entry = {
        "ts": _now(),
        "agent_id": (agent_id or "").strip() or "unknown",
        "capability": (capability or "").strip(),
        "allowed": bool(allowed),
        "reason": (reason or "")[:500],
        "resource": (resource or "")[:300] or None,
        "meta": meta or {},
    }
    try:
        with _LOCK:
            path = _path()
            path.parent.mkdir(parents=True, exist_ok=True)
            with path.open("a", encoding="utf-8") as fh:
                fh.write(json.dumps(entry, ensure_ascii=False) + "\n")
    except Exception as exc:
        logger.warning("trust_graph write failed: %s", exc)
    return entry


def list_recent(
    *,
    limit: int = 50,
    agent_id: str | None = None,
    allowed: bool | None = None,
) -> list[dict[str, Any]]:
    """Return newest-first decisions (best-effort scan of jsonl tail)."""
    lim = max(1, min(int(limit), _MAX_READ))
    path = _path()
    if not path.exists():
        return []
    rows: list[dict[str, Any]] = []
    try:
        with _LOCK:
            lines = path.read_text(encoding="utf-8").splitlines()
        for line in reversed(lines[-(_MAX_READ * 2) :]):
            line = line.strip()
            if not line:
                continue
            try:
                row = json.loads(line)
            except Exception:
                continue
            if agent_id and row.get("agent_id") != agent_id:
                continue
            if allowed is not None and bool(row.get("allowed")) != allowed:
                continue
            rows.append(row)
            if len(rows) >= lim:
                break
    except Exception as exc:
        logger.warning("trust_graph read failed: %s", exc)
    return rows
