"""Local coding error journal — patterns QA + pipeline (backup + gate metrics)."""

from __future__ import annotations

import json
import logging
import os
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

_PROJECT_ROOT = Path(__file__).resolve().parent.parent


def _journal_path() -> Path:
    return Path(
        os.getenv("CODING_ERRORS_PATH", str(_PROJECT_ROOT / "data" / "coding_errors.json"))
    )


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _default_journal() -> dict[str, Any]:
    return {
        "version": 1,
        "updated_at": _now_iso(),
        "entries": [],
        "patterns": {},
    }


def load_journal() -> dict[str, Any]:
    path = _journal_path()
    if not path.is_file():
        data = _default_journal()
        save_journal(data)
        return data
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        logger.warning("[CodingErrors] read failed: %s", exc)
        return _default_journal()


def save_journal(data: dict[str, Any]) -> Path:
    path = _journal_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    data["updated_at"] = _now_iso()
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")
    return path


def _pattern_key(error_type: str, message: str) -> str:
    base = re.sub(r"\d+", "#", message.lower())[:120]
    return f"{error_type}:{base}"


def record_coding_error(
    *,
    agent_name: str,
    task_id: str | None,
    repo_slug: str | None,
    error_type: str,
    error_message: str,
    qa_errors: list[str] | None = None,
    status: str = "open",
    solution: str | None = None,
) -> dict[str, Any]:
    """Append an entry to data/coding_errors.json and update pattern counts."""
    journal = load_journal()
    entry_id = f"{len(journal['entries']) + 1:05d}"
    entry: dict[str, Any] = {
        "id": entry_id,
        "agent_name": agent_name,
        "task_id": task_id,
        "repo_slug": repo_slug,
        "error_type": error_type,
        "error_message": error_message[:2000],
        "qa_errors": (qa_errors or [])[:10],
        "status": status,
        "solution": (solution or "")[:2000] or None,
        "created_at": _now_iso(),
        "resolved_at": _now_iso() if status == "resolved" else None,
    }
    journal["entries"].append(entry)

    key = _pattern_key(error_type, error_message)
    patterns: dict[str, Any] = journal.setdefault("patterns", {})
    pat = patterns.setdefault(
        key,
        {"error_type": error_type, "count": 0, "resolved": 0, "sample": error_message[:200]},
    )
    pat["count"] = int(pat.get("count", 0)) + 1
    if status == "resolved":
        pat["resolved"] = int(pat.get("resolved", 0)) + 1

    save_journal(journal)
    return entry


def resolve_matching_errors(
    task_id: str | None,
    error_type: str | None,
    solution: str,
) -> int:
    """Mark open entries resolved when a retry succeeds."""
    journal = load_journal()
    resolved = 0
    for entry in journal.get("entries", []):
        if entry.get("status") != "open":
            continue
        if task_id and entry.get("task_id") == task_id:
            entry["status"] = "resolved"
            entry["solution"] = solution[:2000]
            entry["resolved_at"] = _now_iso()
            resolved += 1
        elif error_type and entry.get("error_type") == error_type and not task_id:
            entry["status"] = "resolved"
            entry["solution"] = solution[:2000]
            entry["resolved_at"] = _now_iso()
            resolved += 1
    if resolved:
        save_journal(journal)
    return resolved


def purge_open_errors(*, note: str = "archived — hub cleanup") -> int:
    """Mark all open journal entries resolved (ops reset)."""
    journal = load_journal()
    resolved = 0
    for entry in journal.get("entries", []):
        if entry.get("status") != "open":
            continue
        entry["status"] = "resolved"
        entry["solution"] = note[:2000]
        entry["resolved_at"] = _now_iso()
        resolved += 1
    if resolved:
        save_journal(journal)
    return resolved


def list_open_errors(
    *,
    repo_slug: str | None = None,
    agent_name: str | None = None,
    limit: int = 50,
) -> list[dict[str, Any]]:
    from services.company_errors import list_open_errors as unified_list

    return unified_list(repo_slug=repo_slug, agent_name=agent_name, limit=limit)


def count_open_errors(
    *,
    repo_slug: str | None = None,
    agent_name: str | None = None,
) -> int:
    from services.company_errors import count_open_errors as unified_count

    return unified_count(repo_slug=repo_slug, agent_name=agent_name)


def count_resolved() -> int:
    journal = load_journal()
    return sum(1 for e in journal.get("entries", []) if e.get("status") == "resolved" and e.get("solution"))


def get_top_patterns(limit: int = 5) -> list[dict[str, Any]]:
    journal = load_journal()
    patterns = list((journal.get("patterns") or {}).values())
    patterns.sort(key=lambda p: int(p.get("count", 0)), reverse=True)
    return patterns[:limit]


def get_human_lessons(limit: int = 8) -> list[dict[str, Any]]:
    """Resolved lessons (human fixes + successful solutions) newest first."""
    journal = load_journal()
    entries = [
        e
        for e in journal.get("entries", [])
        if e.get("status") == "resolved" and (e.get("solution") or "").strip()
    ]
    entries.sort(key=lambda e: e.get("resolved_at") or e.get("created_at") or "", reverse=True)
    return entries[:limit]


def build_lessons_block(limit: int = 8) -> str:
    """Inject QA failures + human lessons into coding prompts."""
    patterns = get_top_patterns(min(limit, 5))
    lessons = get_human_lessons(limit)
    if not patterns and not lessons:
        return ""
    lines = ["\n⚠️ LEÇONS CODING ACADEMY (obligatoires — ne pas répéter) :\n"]
    idx = 1
    for entry in lessons:
        etype = entry.get("error_type", "?")
        cause = (entry.get("error_message") or "")[:160]
        fix = (entry.get("solution") or "")[:200]
        lines.append(f"{idx}. [{etype}] {cause}")
        if fix:
            lines.append(f"   → Fix: {fix}")
        idx += 1
    for pat in patterns:
        if idx > limit + 3:
            break
        lines.append(
            f"{idx}. [pattern×{pat.get('count', 1)}] {pat.get('sample', '')[:180]}"
        )
        idx += 1
    lines.append("")
    return "\n".join(lines)
