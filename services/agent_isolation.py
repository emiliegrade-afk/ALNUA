"""Agent isolation façade — locks + slots for coding / parallel / plans (DEC-022)."""

from __future__ import annotations

import logging
import uuid
from contextlib import contextmanager
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterator

from services.execution_slots import (
    SlotBusyError,
    acquire_slot,
    release_slot,
    release_slots_for_holder,
)
from services.resource_locks import (
    LockBusyError,
    LockDeniedError,
    acquire,
    make_key,
    release_all,
)

logger = logging.getLogger(__name__)

__all__ = [
    "IsolationLease",
    "LockBusyError",
    "LockDeniedError",
    "SlotBusyError",
    "coding_isolation",
    "infer_lock_keys",
    "isolation_enabled",
    "repo_key_from_path",
    "task_isolation",
]


def isolation_enabled() -> bool:
    try:
        from config.settings import get_settings

        return bool(getattr(get_settings(), "isolation_enabled", True))
    except Exception:
        return True


def _wait_s() -> float:
    try:
        from config.settings import get_settings

        return float(getattr(get_settings(), "isolation_wait_s", 30.0))
    except Exception:
        return 30.0


def repo_key_from_path(repo_path: str | None) -> str | None:
    if not repo_path:
        return None
    try:
        return Path(repo_path).resolve().name.lower()
    except Exception:
        return Path(str(repo_path)).name.lower() or None


def infer_lock_keys(
    *,
    agent_id: str = "",
    kwargs: dict[str, Any] | None = None,
    lock_keys: list[str] | None = None,
) -> list[str]:
    """Derive resource keys from explicit list + common kwargs fields."""
    keys: list[str] = []
    seen: set[str] = set()

    def _add(k: str) -> None:
        if k and k not in seen:
            seen.add(k)
            keys.append(k)

    for k in lock_keys or []:
        try:
            from services.resource_locks import normalize_key

            _add(normalize_key(str(k)))
        except Exception:
            continue

    kw = kwargs or {}
    for field_name, kind in (
        ("ticket_id", "ticket"),
        ("issue_number", "ticket"),
        ("dossier_id", "dossier"),
        ("campaign_id", "campaign"),
        ("task_id", "task"),
        ("error_id", "task"),
    ):
        val = kw.get(field_name)
        if val is not None and str(val).strip():
            _add(make_key(kind, str(val).strip()))

    data_file = kw.get("data_file") or kw.get("json_path")
    if data_file:
        _add(make_key("data", Path(str(data_file)).name))

    for path in list(kw.get("files_to_modify") or []) + list(kw.get("files_to_create") or []):
        p = str(path).strip().replace("\\", "/").lstrip("/")
        if p:
            _add(make_key("path", p))

    # Soft per-agent exec mutex is handled by slots (max_per_agent), not a lock key.
    _ = agent_id
    return keys


@dataclass
class IsolationLease:
    holder_id: str
    agent_id: str
    lock_keys: list[str] = field(default_factory=list)
    slot_token: str | None = None
    repo_key: str | None = None

    def release(self) -> None:
        n = release_all(self.holder_id)
        if self.slot_token:
            release_slot(self.slot_token)
            self.slot_token = None
        else:
            release_slots_for_holder(self.holder_id)
        logger.debug(
            "agent_isolation: released holder=%s locks=%s",
            self.holder_id,
            n,
        )


def _acquire_lease(
    *,
    agent_id: str,
    holder_id: str,
    lock_keys: list[str],
    repo_key: str | None,
    wait_s: float,
    meta: dict[str, Any] | None = None,
) -> IsolationLease:
    lease = IsolationLease(
        holder_id=holder_id,
        agent_id=agent_id,
        lock_keys=list(lock_keys),
        repo_key=repo_key,
    )
    acquired: list[str] = []
    try:
        for key in lock_keys:
            acquire(
                key,
                holder_id=holder_id,
                agent_id=agent_id,
                wait_s=wait_s,
                meta=meta,
            )
            acquired.append(key)
        token = acquire_slot(
            agent_id=agent_id,
            holder_id=holder_id,
            repo_key=repo_key,
            wait_s=wait_s,
            meta=meta,
        )
        lease.slot_token = token
        return lease
    except Exception:
        release_all(holder_id)
        if lease.slot_token:
            release_slot(lease.slot_token)
        raise


@contextmanager
def task_isolation(
    *,
    agent_id: str,
    holder_id: str | None = None,
    lock_keys: list[str] | None = None,
    kwargs: dict[str, Any] | None = None,
    repo_path: str | None = None,
    repo_slug: str | None = None,
    wait_s: float | None = None,
    meta: dict[str, Any] | None = None,
) -> Iterator[IsolationLease | None]:
    """Acquire locks+slot for a generic agent task. No-op if isolation disabled."""
    if not isolation_enabled():
        yield None
        return

    hid = (holder_id or "").strip() or f"task-{uuid.uuid4().hex[:10]}"
    keys = infer_lock_keys(agent_id=agent_id, kwargs=kwargs, lock_keys=lock_keys)
    repo = (repo_slug or "").strip().lower() or repo_key_from_path(repo_path)
    wait = float(wait_s if wait_s is not None else _wait_s())
    lease = _acquire_lease(
        agent_id=agent_id,
        holder_id=hid,
        lock_keys=keys,
        repo_key=repo,
        wait_s=wait,
        meta=meta,
    )
    try:
        yield lease
    finally:
        lease.release()


@contextmanager
def coding_isolation(spec: dict[str, Any]) -> Iterator[IsolationLease | None]:
    """Isolation scope for a coding worktree run."""
    if not isolation_enabled():
        yield None
        return

    agent_id = str(spec.get("agent_id") or "dev_app").strip()
    try:
        from services.permission_guard import PermissionDeniedError, require_capability

        require_capability(
            agent_id,
            "coding:worktree",
            resource=str(spec.get("task_id") or "")[:120] or None,
            meta={"kind": "coding_isolation"},
        )
        require_capability(
            agent_id,
            "git:commit",
            resource=str(spec.get("task_id") or "")[:120] or None,
            meta={"kind": "coding_isolation"},
        )
        require_capability(
            agent_id,
            "git:push:feature",
            resource=str(spec.get("task_id") or "")[:120] or None,
            meta={"kind": "coding_isolation"},
        )
    except PermissionDeniedError:
        raise
    except Exception:
        pass

    task_id = str(spec.get("task_id") or uuid.uuid4().hex[:8]).strip()
    holder_id = f"coding:{agent_id}:{task_id}"
    kw = {
        "task_id": task_id,
        "ticket_id": spec.get("ticket_id") or spec.get("issue_number"),
        "files_to_modify": spec.get("files_to_modify") or [],
        "files_to_create": spec.get("files_to_create") or [],
    }
    keys = infer_lock_keys(agent_id=agent_id, kwargs=kw)
    # Always lock the coding task id so two runners cannot claim the same issue.
    task_key = make_key("task", task_id)
    if task_key not in keys:
        keys.insert(0, task_key)

    repo = str(spec.get("repo_slug") or "").strip().lower() or repo_key_from_path(
        str(spec.get("repo_path") or "")
    )
    wait = _wait_s()
    lease = _acquire_lease(
        agent_id=agent_id,
        holder_id=holder_id,
        lock_keys=keys,
        repo_key=repo,
        wait_s=wait,
        meta={"kind": "coding", "title": str(spec.get("title") or "")[:80]},
    )
    try:
        yield lease
    finally:
        lease.release()
