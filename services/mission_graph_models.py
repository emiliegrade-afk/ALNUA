"""Mission Graph domain models — Phase B (DEC-023)."""

from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Literal

TaskStatus = Literal[
    "PENDING",
    "READY",
    "EXECUTING",
    "COMPLETED",
    "FAILED",
    "BLOCKED",
    "A_VERIFIER",
    "SKIPPED",
]

MissionStatus = Literal[
    "DRAFTED",
    "IN_PROGRESS",
    "BLOCKED",
    "COMPLETED",
    "FAILED",
    "A_VERIFIER",
    "CANCELLED",
]

_TERMINAL_OK = frozenset({"COMPLETED", "SKIPPED", "A_VERIFIER"})
_TERMINAL_ALL = frozenset({"COMPLETED", "FAILED", "BLOCKED", "SKIPPED", "A_VERIFIER"})


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def new_mission_id() -> str:
    return f"mis_{int(time.time())}_{uuid.uuid4().hex[:6]}"


@dataclass
class MissionTask:
    task_id: str
    description: str
    agent_id: str
    method: str
    kwargs: dict[str, Any] = field(default_factory=dict)
    depends_on: list[str] = field(default_factory=list)
    status: TaskStatus = "PENDING"
    lock_keys: list[str] = field(default_factory=list)
    repo_slug: str = ""
    repo_path: str = ""
    project_id: str | None = None
    result: Any = None
    error: str | None = None
    started_at: str | None = None
    finished_at: str | None = None
    duration_ms: int = 0
    retries: int = 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "task_id": self.task_id,
            "description": self.description,
            "agent_id": self.agent_id,
            "method": self.method,
            "kwargs": self.kwargs,
            "depends_on": list(self.depends_on),
            "status": self.status,
            "lock_keys": list(self.lock_keys),
            "repo_slug": self.repo_slug,
            "repo_path": self.repo_path,
            "project_id": self.project_id,
            "result": self.result,
            "error": self.error,
            "started_at": self.started_at,
            "finished_at": self.finished_at,
            "duration_ms": self.duration_ms,
            "retries": self.retries,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> MissionTask:
        return cls(
            task_id=str(data["task_id"]),
            description=str(data.get("description") or ""),
            agent_id=str(data.get("agent_id") or ""),
            method=str(data.get("method") or ""),
            kwargs=dict(data.get("kwargs") or {}),
            depends_on=[str(d) for d in (data.get("depends_on") or [])],
            status=data.get("status") or "PENDING",  # type: ignore[arg-type]
            lock_keys=[str(k) for k in (data.get("lock_keys") or [])],
            repo_slug=str(data.get("repo_slug") or ""),
            repo_path=str(data.get("repo_path") or ""),
            project_id=data.get("project_id"),
            result=data.get("result"),
            error=data.get("error"),
            started_at=data.get("started_at"),
            finished_at=data.get("finished_at"),
            duration_ms=int(data.get("duration_ms") or 0),
            retries=int(data.get("retries") or 0),
        )


@dataclass
class MissionProject:
    project_id: str
    title: str
    depends_on: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "project_id": self.project_id,
            "title": self.title,
            "depends_on": list(self.depends_on),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> MissionProject:
        return cls(
            project_id=str(data["project_id"]),
            title=str(data.get("title") or ""),
            depends_on=[str(d) for d in (data.get("depends_on") or [])],
        )


@dataclass
class Mission:
    mission_id: str
    title: str
    objective: str = ""
    status: MissionStatus = "DRAFTED"
    tasks: list[MissionTask] = field(default_factory=list)
    projects: list[MissionProject] = field(default_factory=list)
    context: str = ""
    created_at: str = field(default_factory=_now_iso)
    updated_at: str = field(default_factory=_now_iso)
    started_at: str | None = None
    finished_at: str | None = None
    source: str = "manual"  # manual | coo_plan | from_plan

    def task_map(self) -> dict[str, MissionTask]:
        return {t.task_id: t for t in self.tasks}

    def to_dict(self) -> dict[str, Any]:
        return {
            "mission_id": self.mission_id,
            "title": self.title,
            "objective": self.objective,
            "status": self.status,
            "context": self.context,
            "source": self.source,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "started_at": self.started_at,
            "finished_at": self.finished_at,
            "projects": [p.to_dict() for p in self.projects],
            "tasks": [t.to_dict() for t in self.tasks],
            "graph": self.graph_summary(),
        }

    def graph_summary(self) -> dict[str, Any]:
        edges = []
        for t in self.tasks:
            for dep in t.depends_on:
                edges.append({"from": dep, "to": t.task_id})
        by_status: dict[str, int] = {}
        for t in self.tasks:
            by_status[t.status] = by_status.get(t.status, 0) + 1
        return {
            "nodes": [
                {
                    "id": t.task_id,
                    "agent_id": t.agent_id,
                    "status": t.status,
                    "label": t.description[:80],
                }
                for t in self.tasks
            ],
            "edges": edges,
            "by_status": by_status,
            "progress_pct": self.progress_pct(),
        }

    def progress_pct(self) -> int:
        if not self.tasks:
            return 0
        done = sum(1 for t in self.tasks if t.status in _TERMINAL_OK)
        return int(100 * done / len(self.tasks))

    def recompute_status(self) -> MissionStatus:
        if self.status == "CANCELLED":
            return self.status
        if not self.tasks:
            self.status = "DRAFTED"
            return self.status
        statuses = {t.status for t in self.tasks}
        if all(s in _TERMINAL_OK for s in statuses):
            if any(t.status == "A_VERIFIER" for t in self.tasks):
                self.status = "A_VERIFIER"
            else:
                self.status = "COMPLETED"
            return self.status
        if any(t.status == "EXECUTING" for t in self.tasks) or any(
            t.status == "READY" for t in self.tasks
        ):
            self.status = "IN_PROGRESS"
            return self.status
        if any(t.status == "FAILED" for t in self.tasks) and all(
            t.status in _TERMINAL_ALL for t in self.tasks
        ):
            self.status = "FAILED"
            return self.status
        if any(t.status == "BLOCKED" for t in self.tasks) and not any(
            t.status in {"PENDING", "READY", "EXECUTING"} for t in self.tasks
        ):
            # Remaining are blocked/failed/done
            if any(t.status == "FAILED" for t in self.tasks):
                self.status = "FAILED"
            else:
                self.status = "BLOCKED"
            return self.status
        if any(t.status != "PENDING" for t in self.tasks):
            self.status = "IN_PROGRESS"
        else:
            self.status = "DRAFTED"
        return self.status

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Mission:
        return cls(
            mission_id=str(data["mission_id"]),
            title=str(data.get("title") or ""),
            objective=str(data.get("objective") or ""),
            status=data.get("status") or "DRAFTED",  # type: ignore[arg-type]
            tasks=[MissionTask.from_dict(t) for t in (data.get("tasks") or [])],
            projects=[MissionProject.from_dict(p) for p in (data.get("projects") or [])],
            context=str(data.get("context") or ""),
            created_at=str(data.get("created_at") or _now_iso()),
            updated_at=str(data.get("updated_at") or _now_iso()),
            started_at=data.get("started_at"),
            finished_at=data.get("finished_at"),
            source=str(data.get("source") or "manual"),
        )
