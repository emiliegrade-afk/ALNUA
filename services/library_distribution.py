"""Library distribution ledger — track Mem0 fanout + agent learning per entry."""

from __future__ import annotations

import json
import logging
import threading
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Literal

from services.team_enrichment import BUREAU_AGENTS, agents_for_bureau

logger = logging.getLogger(__name__)

ROOT = Path(__file__).resolve().parent.parent
LEDGER_FILE = ROOT / "data" / "library_distribution.json"
_LOCK = threading.Lock()
_BATCH_MODE = False
_PENDING_RECEIPTS: dict[str, dict[str, Any]] = {}
_CANCEL_ACTIVE_JOB = False

_STATUS_CACHE: dict[str, Any] | None = None
_STATUS_CACHE_AT: float = 0.0
_STATUS_CACHE_TTL = 25.0

JobKind = Literal["distribute_all", "learn_pending", "verify_all"]
JobStatus = Literal["queued", "running", "completed", "failed"]


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _empty_ledger() -> dict[str, Any]:
    return {"version": 1, "receipts": {}, "jobs": {}}


def _load_ledger() -> dict[str, Any]:
    if not LEDGER_FILE.is_file():
        return _empty_ledger()
    try:
        data = json.loads(LEDGER_FILE.read_text(encoding="utf-8"))
        data.setdefault("receipts", {})
        data.setdefault("jobs", {})
        return data
    except Exception as exc:
        logger.warning("library_distribution load failed: %s", exc)
        return _empty_ledger()


def _save_ledger(data: dict[str, Any]) -> None:
    LEDGER_FILE.parent.mkdir(parents=True, exist_ok=True)
    LEDGER_FILE.write_text(
        json.dumps(data, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    global _STATUS_CACHE
    _STATUS_CACHE = None


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


def cancel_active_job() -> dict[str, Any]:
    global _CANCEL_ACTIVE_JOB
    ledger = _load_ledger()
    active = _active_job_snapshot(ledger)
    if not active:
        return {"success": False, "message": "Aucun job en cours."}
    _CANCEL_ACTIVE_JOB = True
    _update_job(
        active["id"],
        status="failed",
        finished_at=_utc_now(),
        message="Annulé par l'utilisateur.",
    )
    end_batch_mode()
    return {"success": True, "message": "Job annulé.", "job_id": active["id"]}


def _job_cancelled() -> bool:
    return _CANCEL_ACTIVE_JOB


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


def _load_all_entries() -> list[dict[str, Any]]:
    from services.bureau_library import LIBRARY_FILE

    if not LIBRARY_FILE.is_file():
        return []
    try:
        store = json.loads(LIBRARY_FILE.read_text(encoding="utf-8"))
        return list(store.get("entries", []))
    except Exception:
        return []


def expected_slots_for_entry(entry: dict[str, Any]) -> list[str]:
    return agents_for_bureau(str(entry.get("bureau") or "hub"))


def get_distribution_status(*, force: bool = False) -> dict[str, Any]:
    """CEO dashboard — cached to avoid blocking API on 4k+ entries."""
    global _STATUS_CACHE, _STATUS_CACHE_AT
    now = time.monotonic()
    if (
        not force
        and _STATUS_CACHE
        and (now - _STATUS_CACHE_AT) < _STATUS_CACHE_TTL
    ):
        cached = dict(_STATUS_CACHE)
        cached["active_job"] = _active_job_snapshot(_load_ledger())
        cached["cached"] = True
        return cached

    entries = _load_all_entries()
    ledger = _load_ledger()
    receipts: dict[str, dict[str, Any]] = ledger.get("receipts", {})

    total_entries = len(entries)
    total_slots = 0
    distributed_slots = 0
    learned_slots = 0
    verified_slots = 0
    mem0_confirmed = 0
    entries_fully_distributed = 0
    entries_fully_learned = 0
    entries_fully_verified = 0
    by_bureau: dict[str, dict[str, int]] = {}

    for entry in entries:
        entry_id = str(entry.get("id") or "")
        bureau = str(entry.get("bureau") or "hub")
        agents = expected_slots_for_entry(entry)
        bureau_stats = by_bureau.setdefault(
            bureau,
            {
                "entries": 0,
                "slots": 0,
                "distributed": 0,
                "learned": 0,
                "verified": 0,
            },
        )
        bureau_stats["entries"] += 1

        all_dist = True
        all_learned = True
        all_verified = True

        for agent_id in agents:
            total_slots += 1
            bureau_stats["slots"] += 1
            row = receipts.get(receipt_key(entry_id, agent_id), {})

            if row.get("distributed_at"):
                distributed_slots += 1
                bureau_stats["distributed"] += 1
            else:
                all_dist = False

            if row.get("learned_at"):
                learned_slots += 1
                bureau_stats["learned"] += 1
            else:
                all_learned = False

            if row.get("verified_at"):
                verified_slots += 1
                bureau_stats["verified"] += 1
                if row.get("mem0_found"):
                    mem0_confirmed += 1
                else:
                    all_verified = False
            else:
                all_verified = False

        if all_dist and agents:
            entries_fully_distributed += 1
        if all_learned and agents:
            entries_fully_learned += 1
        if all_verified and agents:
            entries_fully_verified += 1

    active_job = _active_job_snapshot(ledger)

    from services.bureau_library import list_entries

    lib_meta = list_entries(limit=0)
    now_count = lib_meta.get("counts_by_timing", {}).get("now", 0)

    def pct(num: int, den: int) -> float:
        return round((num / den * 100) if den else 0.0, 1)

    result = {
        "total_entries": total_entries,
        "library_entries": total_entries,
        "library_now": now_count,
        "total_slots": total_slots,
        "distributed_slots": distributed_slots,
        "learned_slots": learned_slots,
        "verified_slots": verified_slots,
        "mem0_confirmed_slots": mem0_confirmed,
        "entries_fully_distributed": entries_fully_distributed,
        "entries_fully_learned": entries_fully_learned,
        "entries_fully_verified": entries_fully_verified,
        "entries_pending_distribution": total_entries - entries_fully_distributed,
        "distribution_pct": pct(distributed_slots, total_slots),
        "learned_pct": pct(learned_slots, total_slots),
        "verified_pct": pct(mem0_confirmed, total_slots),
        "agents_total": sum(len(v) for v in BUREAU_AGENTS.values()),
        "agents_with_memories": learned_slots,
        "bureaus": len(BUREAU_AGENTS),
        "by_bureau": by_bureau,
        "active_job": active_job,
        "ledger_receipts": len(receipts),
        "cached": False,
    }
    _STATUS_CACHE = result
    _STATUS_CACHE_AT = now
    return result


def _active_job_snapshot(ledger: dict[str, Any]) -> dict[str, Any] | None:
    jobs = ledger.get("jobs", {})
    running = [
        j for j in jobs.values() if j.get("status") in ("queued", "running")
    ]
    if not running:
        return None
    running.sort(key=lambda j: j.get("started_at", ""), reverse=True)
    return running[0]


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


def verify_entry_in_mem0(entry: dict[str, Any], agent_id: str) -> bool:
    """Check whether a library entry actually landed in Mem0 for an agent.

    Mem0's search is semantic (vector nearest-neighbor), so querying with the
    entry's own UUID — a string with no semantic content — almost never
    surfaces the right memory once an agent has more than a handful of
    entries. Querying with the entry's real title instead reuses the same
    text that was embedded at write time (see `_memory_line`), which is what
    actually gives the vector search something to match on.
    """
    entry_id = str(entry.get("id") or "")
    query = str(entry.get("title") or "").strip() or f"library:{entry_id}"
    try:
        from skills.skill_mem0 import recall

        snippet = recall(query, agent_id=agent_id)
        found = bool(snippet) and f"library:{entry_id}".lower() in snippet.lower()
        record_verified(entry_id, agent_id, mem0_found=found)
        return found
    except Exception as exc:
        logger.debug("verify_entry_in_mem0 failed %s/%s: %s", entry_id, agent_id, exc)
        record_verified(entry_id, agent_id, mem0_found=False)
        return False


def _run_distribute_all_job(
    job_id: str,
    *,
    skip_distributed: bool,
    timing: str | None,
    run_learning: bool,
) -> None:
    global _CANCEL_ACTIVE_JOB
    _CANCEL_ACTIVE_JOB = False
    from services.team_enrichment import fanout_library_entry

    entries = _load_all_entries()
    if timing in ("now", "later"):
        entries = [e for e in entries if e.get("timing") == timing]

    _update_job(job_id, status="running", total=len(entries), message="Distribution en cours…")
    distributed_count = 0
    learned_count = 0
    errors = 0

    begin_batch_mode()
    try:
        for i, entry in enumerate(entries):
            if _job_cancelled():
                break
            entry_id = str(entry.get("id") or "")
            try:
                agents = fanout_library_entry(
                    entry,
                    distill_lessons=False,
                    skip_if_distributed=skip_distributed,
                )
                distributed_count += len(agents)
            except Exception as exc:
                errors += 1
                logger.debug("distribute entry %s failed: %s", entry_id, exc)

            if (i + 1) % 25 == 0 or i + 1 == len(entries):
                _update_job(
                    job_id,
                    processed=i + 1,
                    distributed=distributed_count,
                    learned=learned_count,
                    errors=errors,
                    message=f"{i + 1}/{len(entries)} fiches traitées",
                )
                get_distribution_status(force=True)
                time.sleep(0.05)
    finally:
        end_batch_mode()

    if _job_cancelled():
        return

    _update_job(
        job_id,
        status="completed",
        processed=len(entries),
        distributed=distributed_count,
        learned=learned_count,
        errors=errors,
        finished_at=_utc_now(),
        message=(
            f"Distribution terminée — {distributed_count} diffusion(s) Mem0, "
            f"{errors} erreur(s)."
        ),
    )
    get_distribution_status(force=True)

    if run_learning and distributed_count > 0:
        learn_id = _create_job("learn_pending", 0)
        threading.Thread(
            target=_run_learn_pending_job,
            args=(learn_id,),
            daemon=True,
        ).start()


def _run_learn_pending_job(job_id: str) -> None:
    from services.team_enrichment import distill_library_entry_for_agent

    entries = _load_all_entries()
    ledger = _load_ledger()
    receipts = ledger.get("receipts", {})

    pending: list[tuple[dict[str, Any], str]] = []
    for entry in entries:
        entry_id = str(entry.get("id") or "")
        for agent_id in expected_slots_for_entry(entry):
            row = receipts.get(receipt_key(entry_id, agent_id), {})
            if row.get("distributed_at") and not row.get("learned_at"):
                pending.append((entry, agent_id))

    _update_job(
        job_id,
        status="running",
        total=len(pending),
        message="Apprentissage des fiches distribuées…",
    )
    learned_count = 0
    errors = 0

    for i, (entry, agent_id) in enumerate(pending):
        try:
            if distill_library_entry_for_agent(entry, agent_id, blocking=True):
                learned_count += 1
        except Exception as exc:
            errors += 1
            logger.debug("learn pending failed: %s", exc)

        if (i + 1) % 10 == 0 or i + 1 == len(pending):
            _update_job(
                job_id,
                processed=i + 1,
                learned=learned_count,
                errors=errors,
                message=f"{i + 1}/{len(pending)} apprentissages",
            )

    _update_job(
        job_id,
        status="completed",
        processed=len(pending),
        learned=learned_count,
        errors=errors,
        finished_at=_utc_now(),
        message=f"Terminé — {learned_count} leçon(s) distillée(s).",
    )


def _run_verify_all_job(job_id: str) -> None:
    entries = _load_all_entries()
    ledger = _load_ledger()
    receipts = ledger.get("receipts", {})

    pairs: list[tuple[dict[str, Any], str]] = []
    for entry in entries:
        entry_id = str(entry.get("id") or "")
        for agent_id in expected_slots_for_entry(entry):
            row = receipts.get(receipt_key(entry_id, agent_id), {})
            if row.get("distributed_at"):
                pairs.append((entry, agent_id))

    _update_job(
        job_id,
        status="running",
        total=len(pairs),
        message="Vérification Mem0…",
    )
    verified = 0
    confirmed = 0
    errors = 0

    for i, (entry, agent_id) in enumerate(pairs):
        try:
            if verify_entry_in_mem0(entry, agent_id):
                confirmed += 1
            verified += 1
        except Exception:
            errors += 1

        if (i + 1) % 50 == 0 or i + 1 == len(pairs):
            _update_job(
                job_id,
                processed=i + 1,
                verified=verified,
                distributed=confirmed,
                errors=errors,
                message=f"{i + 1}/{len(pairs)} vérifications",
            )

    _update_job(
        job_id,
        status="completed",
        processed=len(pairs),
        verified=verified,
        distributed=confirmed,
        errors=errors,
        finished_at=_utc_now(),
        message=f"Terminé — {confirmed}/{len(pairs)} confirmé(s) dans Mem0.",
    )


def start_distribute_all_job(
    *,
    skip_distributed: bool = True,
    timing: str | None = None,
    run_learning: bool = True,
) -> dict[str, Any]:
    entries = _load_all_entries()
    if timing in ("now", "later"):
        entries = [e for e in entries if e.get("timing") == timing]

    if _active_job_snapshot(_load_ledger()):
        return {
            "success": False,
            "message": "Un job est déjà en cours — attends la fin ou rafraîchis le statut.",
        }

    job_id = _create_job("distribute_all", len(entries))
    threading.Thread(
        target=_run_distribute_all_job,
        kwargs={
            "job_id": job_id,
            "skip_distributed": skip_distributed,
            "timing": timing,
            "run_learning": run_learning,
        },
        daemon=True,
    ).start()
    return {
        "success": True,
        "job_id": job_id,
        "status": get_job(job_id),
        "message": f"Distribution lancée — {len(entries)} fiche(s) en file.",
    }


def start_learn_pending_job() -> dict[str, Any]:
    if _active_job_snapshot(_load_ledger()):
        return {"success": False, "message": "Un job est déjà en cours."}

    job_id = _create_job("learn_pending", 0)
    threading.Thread(target=_run_learn_pending_job, args=(job_id,), daemon=True).start()
    return {
        "success": True,
        "job_id": job_id,
        "status": get_job(job_id),
        "message": "Apprentissage des fiches distribuées lancé.",
    }


def start_verify_all_job() -> dict[str, Any]:
    if _active_job_snapshot(_load_ledger()):
        return {"success": False, "message": "Un job est déjà en cours."}

    job_id = _create_job("verify_all", 0)
    threading.Thread(target=_run_verify_all_job, args=(job_id,), daemon=True).start()
    return {
        "success": True,
        "job_id": job_id,
        "status": get_job(job_id),
        "message": "Vérification Mem0 lancée.",
    }
