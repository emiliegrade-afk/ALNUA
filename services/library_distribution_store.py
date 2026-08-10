"""Library distribution — ledger persistence, receipts, and job records."""

from __future__ import annotations

import json
import logging
import threading
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Literal

logger = logging.getLogger(__name__)

ROOT = Path(__file__).resolve().parent.parent
LEDGER_FILE = ROOT / "data" / "library_distribution.json"
_LOCK = threading.Lock()


def _ledger_path() -> Path:
    """Resolve LEDGER_FILE via façade so tests can monkeypatch one path."""
    from services.library_distribution import LEDGER_FILE as facade_ledger

    return facade_ledger


_BATCH_MODE = False
_PENDING_RECEIPTS: dict[str, dict[str, Any]] = {}

JobKind = Literal["distribute_all", "learn_pending", "verify_all"]
JobStatus = Literal["queued", "running", "completed", "failed"]


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _empty_ledger() -> dict[str, Any]:
    return {"version": 1, "receipts": {}, "jobs": {}}


def _load_ledger() -> dict[str, Any]:
    ledger_file = _ledger_path()
    if not ledger_file.is_file():
        return _empty_ledger()
    try:
        data = json.loads(ledger_file.read_text(encoding="utf-8"))
        data.setdefault("receipts", {})
        data.setdefault("jobs", {})
        return data
    except Exception as exc:
        logger.warning("library_distribution load failed: %s", exc)
        return _empty_ledger()


def _save_ledger(data: dict[str, Any]) -> None:
    ledger_file = _ledger_path()
    ledger_file.parent.mkdir(parents=True, exist_ok=True)
    ledger_file.write_text(
        json.dumps(data, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    from services.library_distribution_status import invalidate_status_cache

    invalidate_status_cache()


def _flush_pending_receipts() -> None:
    global _PENDING_RECEIPTS
    if not _PENDING_RECEIPTS:
        return
    with _LOCK:
        ledger = _load_ledger()
        ledger["receipts"].update(_PENDING_RECEIPTS)
        _save_ledger(ledger)
        _PENDING_RECEIPTS = {}


def begin_batch_mode() -> None:
    global _BATCH_MODE
    _BATCH_MODE = True


def end_batch_mode() -> None:
    global _BATCH_MODE
    _BATCH_MODE = False
    _flush_pending_receipts()


def _queue_receipt(key: str, row: dict[str, Any]) -> None:
    global _PENDING_RECEIPTS
    if _BATCH_MODE:
        _PENDING_RECEIPTS[key] = row
        if len(_PENDING_RECEIPTS) >= 100:
            _flush_pending_receipts()
        return
    with _LOCK:
        ledger = _load_ledger()
        ledger["receipts"][key] = row
        _save_ledger(ledger)


def receipt_key(entry_id: str, agent_id: str) -> str:
    return f"{entry_id}:{agent_id}"


def _get_receipt(entry_id: str, agent_id: str) -> dict[str, Any] | None:
    ledger = _load_ledger()
    return ledger["receipts"].get(receipt_key(entry_id, agent_id))


def record_distributed(entry_id: str, agent_id: str) -> None:
    key = receipt_key(entry_id, agent_id)
    row = {"entry_id": entry_id, "agent_id": agent_id}
    existing = _get_receipt(entry_id, agent_id)
    if existing and existing.get("distributed_at"):
        return
    row["distributed_at"] = _utc_now()
    if existing:
        row = {**existing, **row}
    _queue_receipt(key, row)


def record_learned(entry_id: str, agent_id: str) -> None:
    key = receipt_key(entry_id, agent_id)
    existing = _get_receipt(entry_id, agent_id) or {}
    row = {**existing, "entry_id": entry_id, "agent_id": agent_id, "learned_at": _utc_now()}
    _queue_receipt(key, row)


def record_verified(entry_id: str, agent_id: str, *, mem0_found: bool) -> None:
    key = receipt_key(entry_id, agent_id)
    existing = _get_receipt(entry_id, agent_id) or {}
    row = {
        **existing,
        "entry_id": entry_id,
        "agent_id": agent_id,
        "verified_at": _utc_now(),
        "mem0_found": mem0_found,
    }
    _queue_receipt(key, row)


def is_distributed(entry_id: str, agent_id: str) -> bool:
    row = _get_receipt(entry_id, agent_id)
    return bool(row and row.get("distributed_at"))


def get_job(job_id: str) -> dict[str, Any] | None:
    ledger = _load_ledger()
    return ledger.get("jobs", {}).get(job_id)


def _update_job(job_id: str, **fields: Any) -> None:
    with _LOCK:
        ledger = _load_ledger()
        job = ledger["jobs"].setdefault(job_id, {"id": job_id})
        job.update(fields)
        ledger["jobs"][job_id] = job
        _save_ledger(ledger)


def _create_job(kind: JobKind, total: int) -> str:
    job_id = f"lib_{uuid.uuid4().hex[:12]}"
    with _LOCK:
        ledger = _load_ledger()
        ledger["jobs"][job_id] = {
            "id": job_id,
            "kind": kind,
            "status": "queued",
            "processed": 0,
            "total": total,
            "distributed": 0,
            "learned": 0,
            "verified": 0,
            "errors": 0,
            "message": "En file d'attente…",
            "started_at": _utc_now(),
            "finished_at": None,
        }
        _save_ledger(ledger)
    return job_id


def _active_job_snapshot(ledger: dict[str, Any]) -> dict[str, Any] | None:
    jobs = ledger.get("jobs", {})
    running = [
        j for j in jobs.values() if j.get("status") in ("queued", "running")
    ]
    if not running:
        return None
    running.sort(key=lambda j: j.get("started_at", ""), reverse=True)
    return running[0]
