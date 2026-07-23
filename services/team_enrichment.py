"""
Team enrichment — propagate bureau library findings to all agents via Mem0.

Phase 3: while Academy trains dev_app, the rest of the team learns from research.
"""

from __future__ import annotations

import logging
import threading
from datetime import datetime, timezone
from typing import Any

logger = logging.getLogger(__name__)

# Bureau id → agent ids that should receive library memories
BUREAU_AGENTS: dict[str, list[str]] = {
    "hub": ["coo", "spec", "qa", "pm"],
    "secretary": ["secretary"],
    "app": ["dev_app", "dev_backend"],
    "gaming": ["game_director", "dev_gaming", "level_designer"],
    "robo": ["hardware", "embedded_dev"],
    "marketing": ["marketing", "content"],
    "rd": ["brainstorm", "rnd_agent"],
    "finances": ["accounting", "controller"],
    "analytics": ["analyst_business", "analyst_data"],
    "academy": ["dev_app"],
}


def agents_for_bureau(bureau: str) -> list[str]:
    return list(BUREAU_AGENTS.get(bureau, BUREAU_AGENTS["hub"]))


def _memory_line(entry: dict[str, Any]) -> str:
    from services.bureau_library import BUREAU_LABELS

    entry_id = str(entry.get("id") or "")
    bureau = entry.get("bureau", "hub")
    label = BUREAU_LABELS.get(bureau, bureau)
    tag = "Utile maintenant" if entry.get("timing") == "now" else "À garder pour plus tard"
    title = str(entry.get("title") or "")
    summary = str(entry.get("summary") or "")[:500]
    prefix = f"[library:{entry_id}]" if entry_id else "[library]"
    return f"{prefix} [Bibliothèque {label} — {tag}] {title}\n{summary}"


def distill_library_entry_for_agent(
    entry: dict[str, Any],
    agent_id: str,
    *,
    blocking: bool = False,
) -> bool:
    """Distill a library article into an agent-specific Mem0 lesson."""
    entry_id = str(entry.get("id") or "")
    if not entry_id:
        return False
    task = f"Bibliothèque — {entry.get('title', '')[:120]}"
    outcome = str(entry.get("summary") or entry.get("title") or "")

    def _run() -> bool:
        try:
            from skills.skill_agent_learning import learn_from_outcome
            from services.library_distribution import record_learned

            learn_from_outcome(
                agent_id,
                task,
                outcome,
                success=True,
                blocking=True,
            )
            record_learned(entry_id, agent_id)
            return True
        except Exception as exc:
            logger.debug("distill_library_entry_for_agent failed: %s", exc)
            return False

    if blocking:
        return _run()
    threading.Thread(target=_run, daemon=True).start()
    return True


def fanout_library_entry(
    entry: dict[str, Any],
    *,
    distill_lessons: bool = True,
    skip_if_distributed: bool = False,
) -> list[str]:
    """Write one library entry into Mem0 for every agent in the target bureau."""
    bureau = str(entry.get("bureau") or "hub")
    entry_id = str(entry.get("id") or "")
    agents = agents_for_bureau(bureau)
    memory_text = _memory_line(entry)
    propagated: list[str] = []

    try:
        from skills.skill_mem0 import remember
    except Exception as exc:
        logger.warning("team_enrichment: mem0 unavailable: %s", exc)
        return propagated

    for agent_id in agents:
        if skip_if_distributed and entry_id:
            try:
                from services.library_distribution import is_distributed

                if is_distributed(entry_id, agent_id):
                    continue
            except Exception:
                pass
        try:
            remember(memory_text, agent_id=agent_id)
            propagated.append(agent_id)
            if entry_id:
                try:
                    from services.library_distribution import record_distributed

                    record_distributed(entry_id, agent_id)
                except Exception:
                    pass
        except Exception as exc:
            logger.debug("fanout failed for %s: %s", agent_id, exc)

    if distill_lessons and propagated:
        try:
            for agent_id in propagated:
                if entry.get("timing") == "now":
                    distill_library_entry_for_agent(entry, agent_id, blocking=False)
        except Exception as exc:
            logger.debug("distill lessons skipped: %s", exc)

    return propagated


def enrich_team_from_library(
    *,
    days: int = 30,
    timing: str | None = None,
    limit: int = 25,
) -> dict[str, Any]:
    """Backfill: push recent library entries to all bureau agents."""
    from services.bureau_library import LIBRARY_FILE
    import json

    if not LIBRARY_FILE.is_file():
        return {
            "success": True,
            "entries_processed": 0,
            "agents_enriched": 0,
            "agents": [],
            "message": "Bibliothèque vide — lance une recherche d'abord.",
        }

    store = json.loads(LIBRARY_FILE.read_text(encoding="utf-8"))
    cutoff = datetime.now(timezone.utc).timestamp() - days * 86400
    entries: list[dict[str, Any]] = []
    for raw in store.get("entries", []):
        if timing in ("now", "later") and raw.get("timing") != timing:
            continue
        try:
            ts = datetime.fromisoformat(
                str(raw.get("created_at", "")).replace("Z", "+00:00")
            ).timestamp()
            if ts < cutoff:
                continue
        except Exception:
            pass
        entries.append(raw)

    entries.sort(key=lambda e: e.get("created_at", ""), reverse=True)
    entries = entries[:limit]

    agents_touched: set[str] = set()
    for entry in entries:
        for agent_id in fanout_library_entry(entry, distill_lessons=True):
            agents_touched.add(agent_id)

    agents = sorted(agents_touched)
    return {
        "success": True,
        "entries_processed": len(entries),
        "agents_enriched": len(agents),
        "agents": agents,
        "message": (
            f"{len(entries)} fiche(s) diffusée(s) vers {len(agents)} agent(s)."
            if agents
            else "Aucune fiche récente à diffuser."
        ),
    }


def get_enrichment_status() -> dict[str, Any]:
    """CEO snapshot — library size + distribution coverage."""
    try:
        from services.library_distribution import get_distribution_status

        return get_distribution_status()
    except Exception as exc:
        logger.debug("distribution status fallback: %s", exc)

    from services.bureau_library import list_entries

    lib = list_entries(limit=0)
    total_entries = sum(lib.get("counts_by_bureau", {}).values())
    now_count = lib.get("counts_by_timing", {}).get("now", 0)

    return {
        "library_entries": total_entries,
        "library_now": now_count,
        "agents_with_memories": 0,
        "agents_total": sum(len(v) for v in BUREAU_AGENTS.values()),
        "agent_lessons_hint": {},
        "bureaus": len(BUREAU_AGENTS),
        "distribution_pct": 0.0,
        "learned_pct": 0.0,
        "verified_pct": 0.0,
    }
