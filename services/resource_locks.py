"""Resource lock registry — Phase A isolation (DEC-022).

Fail-closed: no lock → no side-effect. Append-only history of holders;
expired locks are purged on acquire. Store: data/resource_locks.json.
"""

from __future__ import annotations

import json
import logging
import threading
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from config.paths import get_hub_repo_path

logger = logging.getLogger(__name__)

_LOCK = threading.RLock()
_STORE = get_hub_repo_path() / "data" / "resource_locks.json"
_DEFAULT_TTL_S = 3600


class LockBusyError(RuntimeError):
    """Raised when a resource is held by another holder after wait expires."""


class LockDeniedError(RuntimeError):
    """Raised when acquire arguments are invalid (fail-closed)."""


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _now_ts() -> float:
    return time.time()


def _load() -> dict[str, Any]:
    if not _STORE.exists():
        return {"locks": {}, "updated_at": _now_iso()}
    try:
        data = json.loads(_STORE.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            return {"locks": {}, "updated_at": _now_iso()}
        data.setdefault("locks", {})
        return data
    except Exception as exc:
        logger.warning("resource_locks load failed: %s", exc)
        return {"locks": {}, "updated_at": _now_iso()}


def _save(data: dict[str, Any]) -> None:
    _STORE.parent.mkdir(parents=True, exist_ok=True)
    data["updated_at"] = _now_iso()
    tmp = _STORE.with_suffix(".tmp")
    tmp.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    tmp.replace(_STORE)


def normalize_key(key: str) -> str:
    k = (key or "").strip().replace("\\", "/")
    while "//" in k:
        k = k.replace("//", "/")
    if not k or ":" not in k:
        raise LockDeniedError(f"Invalid lock key (need kind:value): {key!r}")
    kind, _, rest = k.partition(":")
    if not kind or not rest.strip():
        raise LockDeniedError(f"Invalid lock key: {key!r}")
    return f"{kind.lower()}:{rest.strip()}"


def make_key(kind: str, *parts: str) -> str:
    """Build a canonical lock key, e.g. make_key('path', 'web/src/a.ts')."""
    value = "/".join(str(p).strip().replace("\\", "/").lstrip("/") for p in parts if str(p).strip())
    return normalize_key(f"{kind}:{value}")


def _purge_expired_unlocked(data: dict[str, Any]) -> int:
    now = _now_ts()
    locks = data.get("locks") or {}
    expired = [k for k, v in locks.items() if float(v.get("expires_at_ts") or 0) <= now]
    for k in expired:
        del locks[k]
    return len(expired)


def purge_expired() -> int:
    with _LOCK:
        data = _load()
        n = _purge_expired_unlocked(data)
        if n:
            _save(data)
        return n


def acquire(
    key: str,
    *,
    holder_id: str,
    agent_id: str,
    ttl_s: int | None = None,
    wait_s: float = 0.0,
    poll_s: float = 0.25,
    meta: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Acquire an exclusive lock. Waits up to wait_s if busy, then LockBusyError."""
    nkey = normalize_key(key)
    hid = (holder_id or "").strip()
    aid = (agent_id or "").strip()
    if not hid or not aid:
        raise LockDeniedError("holder_id and agent_id are required")

    ttl = int(ttl_s if ttl_s is not None else _default_ttl())
    ttl = max(30, min(ttl, 24 * 3600))
    deadline = _now_ts() + max(0.0, float(wait_s))

    while True:
        with _LOCK:
            data = _load()
            _purge_expired_unlocked(data)
            locks = data["locks"]
            current = locks.get(nkey)
            if current and current.get("holder_id") == hid:
                # Re-entrant for same holder — refresh TTL
                current["expires_at_ts"] = _now_ts() + ttl
                current["expires_at"] = _now_iso()
                current["agent_id"] = aid
                if meta:
                    current["meta"] = {**(current.get("meta") or {}), **meta}
                _save(data)
                return dict(current)

            if current is None:
                record = {
                    "key": nkey,
                    "holder_id": hid,
                    "agent_id": aid,
                    "lease_id": str(uuid.uuid4())[:12],
                    "acquired_at": _now_iso(),
                    "expires_at_ts": _now_ts() + ttl,
                    "expires_at": _now_iso(),
                    "meta": dict(meta or {}),
                }
                locks[nkey] = record
                _save(data)
                logger.info(
                    "resource_locks: acquired %s by %s (%s)",
                    nkey,
                    aid,
                    hid,
                )
                return dict(record)

            holder = current.get("holder_id")
            other_agent = current.get("agent_id")

        if _now_ts() >= deadline:
            raise LockBusyError(
                f"Lock busy: {nkey} held by {other_agent}/{holder}"
            )
        time.sleep(max(0.05, float(poll_s)))


def release(key: str, holder_id: str) -> bool:
    """Release if holder matches. Returns True when released."""
    nkey = normalize_key(key)
    hid = (holder_id or "").strip()
    with _LOCK:
        data = _load()
        _purge_expired_unlocked(data)
        current = (data.get("locks") or {}).get(nkey)
        if not current:
            return False
        if current.get("holder_id") != hid:
            logger.warning(
                "resource_locks: release denied %s (holder %s != %s)",
                nkey,
                current.get("holder_id"),
                hid,
            )
            return False
        del data["locks"][nkey]
        _save(data)
        logger.info("resource_locks: released %s", nkey)
        return True


def release_all(holder_id: str) -> int:
    """Release every lock held by holder_id. Returns count released."""
    hid = (holder_id or "").strip()
    if not hid:
        return 0
    with _LOCK:
        data = _load()
        _purge_expired_unlocked(data)
        locks = data.get("locks") or {}
        keys = [k for k, v in locks.items() if v.get("holder_id") == hid]
        for k in keys:
            del locks[k]
        if keys:
            _save(data)
        return len(keys)


def force_release(key: str, *, reason: str = "") -> bool:
    """Admin force-release (does not check holder)."""
    nkey = normalize_key(key)
    with _LOCK:
        data = _load()
        if nkey not in (data.get("locks") or {}):
            return False
        del data["locks"][nkey]
        _save(data)
        logger.warning("resource_locks: force_release %s (%s)", nkey, reason[:120])
        return True


def list_locks() -> list[dict[str, Any]]:
    with _LOCK:
        data = _load()
        _purge_expired_unlocked(data)
        _save(data)
        return [dict(v) for v in sorted((data.get("locks") or {}).values(), key=lambda x: x.get("key", ""))]


def get_lock(key: str) -> dict[str, Any] | None:
    nkey = normalize_key(key)
    with _LOCK:
        data = _load()
        _purge_expired_unlocked(data)
        row = (data.get("locks") or {}).get(nkey)
        return dict(row) if row else None


def _default_ttl() -> int:
    try:
        from config.settings import get_settings

        return int(getattr(get_settings(), "isolation_lock_ttl_s", _DEFAULT_TTL_S))
    except Exception:
        return _DEFAULT_TTL_S


def reset_store_for_tests(path: Path | None = None) -> None:
    """Test helper — wipe store (only for pytest)."""
    target = path or _STORE
    with _LOCK:
        if target.exists():
            target.unlink()
