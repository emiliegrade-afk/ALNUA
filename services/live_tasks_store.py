"""Jarvis Live — persistent task store (SPEC_JARVIS_LIVE §5, DEC-038).

JSON file so tasks survive a Hub restart. Runtime state: ``data/live_tasks.json``
is git-ignored and created on first write.
"""

from __future__ import annotations

import json
import threading
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

STATUS_QUEUED = "queued"
STATUS_RUNNING = "running"
STATUS_DONE = "done"
STATUS_FAILED = "failed"
STATUS_CANCELLED = "cancelled"

ACTIVE_STATUSES = frozenset({STATUS_QUEUED, STATUS_RUNNING})
FINAL_STATUSES = frozenset({STATUS_DONE, STATUS_FAILED, STATUS_CANCELLED})

# Keep the file bounded: oldest *finished* tasks are dropped first.
MAX_STORED_TASKS = 200


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _default_path() -> Path:
    from config.paths import get_hub_repo_path

    return get_hub_repo_path() / "data" / "live_tasks.json"


@dataclass
class LiveTask:
    id: str
    agent_id: str
    instruction: str
    status: str = STATUS_QUEUED
    session_id: str = "live"
    created_at: str = field(default_factory=_now)
    updated_at: str = field(default_factory=_now)
    started_at: str | None = None
    finished_at: str | None = None
    result: str = ""
    artifacts: list[str] = field(default_factory=list)
    file_ids: list[str] = field(default_factory=list)
    error: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class LiveTaskStore:
    """Thread-safe store. One lock guards both memory and disk writes."""

    def __init__(self, path: Path | None = None) -> None:
        self._path = path
        self._lock = threading.RLock()
        self._tasks: dict[str, LiveTask] = {}
        self._loaded = False

    @property
    def path(self) -> Path:
        return self._path or _default_path()

    def _load(self) -> None:
        if self._loaded:
            return
        self._loaded = True
        try:
            raw = json.loads(self.path.read_text(encoding="utf-8"))
            for item in raw.get("tasks", []):
                task = LiveTask(**item)
                self._tasks[task.id] = task
        except FileNotFoundError:
            return
        except (OSError, ValueError, TypeError):
            # A corrupt file must not block the Hub: start empty, keep the bad file aside.
            self._quarantine_corrupt_file()
            return
        self._mark_interrupted()

    def _quarantine_corrupt_file(self) -> None:
        try:
            self.path.replace(self.path.with_suffix(".corrupt.json"))
        except OSError:
            pass

    def _mark_interrupted(self) -> None:
        # The worker pool lives in memory: a task still active at load time cannot
        # be running anymore. Never relaunch silently (SPEC §5.1) — surface the loss.
        changed = False
        for task in self._tasks.values():
            if task.status in ACTIVE_STATUSES:
                task.status = STATUS_FAILED
                task.error = "interrupted_by_restart"
                task.finished_at = task.updated_at = _now()
                changed = True
        if changed:
            self._save()

    def _save(self) -> None:
        self._trim()
        payload = {"tasks": [t.to_dict() for t in self._tasks.values()]}
        try:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            tmp = self.path.with_suffix(".tmp")
            tmp.write_text(json.dumps(payload, ensure_ascii=False, indent=1), encoding="utf-8")
            tmp.replace(self.path)
        except OSError:
            # Persistence is best-effort: the in-memory state stays authoritative.
            pass

    def _trim(self) -> None:
        overflow = len(self._tasks) - MAX_STORED_TASKS
        if overflow <= 0:
            return
        finished = sorted(
            (t for t in self._tasks.values() if t.status in FINAL_STATUSES),
            key=lambda t: t.created_at,
        )
        for task in finished[:overflow]:
            del self._tasks[task.id]

    def add(
        self,
        agent_id: str,
        instruction: str,
        session_id: str = "live",
        file_ids: list[str] | None = None,
    ) -> LiveTask:
        with self._lock:
            self._load()
            task = LiveTask(
                id=uuid.uuid4().hex[:12],
                agent_id=agent_id,
                instruction=instruction,
                session_id=session_id,
                file_ids=list(file_ids or []),
            )
            self._tasks[task.id] = task
            self._save()
            return task

    def get(self, task_id: str) -> LiveTask | None:
        with self._lock:
            self._load()
            return self._tasks.get(task_id)

    def update(self, task_id: str, **fields: Any) -> LiveTask | None:
        with self._lock:
            self._load()
            task = self._tasks.get(task_id)
            if task is None:
                return None
            for key, value in fields.items():
                setattr(task, key, value)
            stamp = datetime.now(timezone.utc)
            try:
                prev = datetime.fromisoformat(task.updated_at)
                if prev.tzinfo is None:
                    prev = prev.replace(tzinfo=timezone.utc)
                if stamp <= prev:
                    stamp = prev + timedelta(microseconds=1)
            except ValueError:
                pass
            task.updated_at = stamp.isoformat()
            self._save()
            return task

    def list_tasks(self, status: str | None = None, limit: int = 50) -> list[LiveTask]:
        with self._lock:
            self._load()
            items = sorted(self._tasks.values(), key=lambda t: t.created_at, reverse=True)
            if status:
                items = [t for t in items if t.status == status]
            return items[:limit]

    def count_active(self) -> int:
        with self._lock:
            self._load()
            return sum(1 for t in self._tasks.values() if t.status in ACTIVE_STATUSES)
