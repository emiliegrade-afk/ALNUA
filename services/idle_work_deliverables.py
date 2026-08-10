"""Idle deliverables — list / read / promote triage drafts to Hub tickets."""

from __future__ import annotations

import json
import logging
from typing import Any

from config.paths import get_hub_repo_path

logger = logging.getLogger(__name__)

_DELIVERABLES = get_hub_repo_path() / "data" / "idle_deliverables"


def list_deliverables(*, limit: int = 30) -> list[dict[str, Any]]:
    if not _DELIVERABLES.exists():
        return []
    files = sorted(_DELIVERABLES.glob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True)
    out: list[dict[str, Any]] = []
    for path in files[: max(1, min(limit, 100))]:
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            continue
        item = data.get("item") or {}
        body = data.get("body") or {}
        out.append(
            {
                "item_id": item.get("id") or path.stem,
                "kind": item.get("kind") or body.get("kind"),
                "title": item.get("title"),
                "agent_id": item.get("agent_id") or body.get("agent_id"),
                "status": item.get("status") or body.get("status"),
                "written_at": data.get("written_at"),
                "preview": _preview_body(body),
                "path": str(path),
            }
        )
    return out


def get_deliverable(item_id: str) -> dict[str, Any] | None:
    path = _DELIVERABLES / f"{item_id}.json"
    if not path.exists():
        # allow stem match if id without prefix
        matches = list(_DELIVERABLES.glob(f"*{item_id}*.json"))
        if not matches:
            return None
        path = matches[0]
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        logger.warning("idle deliverable read failed: %s", exc)
        return None
    data["path"] = str(path)
    return data


def _preview_body(body: dict[str, Any]) -> str:
    if not isinstance(body, dict):
        return str(body)[:240]
    draft = body.get("draft")
    if isinstance(draft, dict) and draft.get("draft"):
        return str(draft.get("draft"))[:240]
    triage = body.get("triage")
    if isinstance(triage, dict):
        summary = triage.get("summary") or ""
        tickets = triage.get("tickets") or []
        return f"{summary} · {len(tickets)} ticket(s)".strip(" ·")[:240]
    if body.get("note"):
        return str(body["note"])[:240]
    if body.get("ops"):
        return str(body["ops"])[:240]
    return json.dumps(body, ensure_ascii=False)[:240]


def offline_triage_tickets() -> list[dict[str, str]]:
    return [
        {
            "title": "[idle-ok] Hub — brancher quick actions App",
            "branch": "hub",
            "priority": "P2",
            "why": "Actions décoratives encore inertes sur /app",
        },
        {
            "title": "[idle-ok] Naïa — triage backlog modules",
            "branch": "app",
            "priority": "P2",
            "why": "Avancer produit App sans brief CEO ponctuel",
        },
        {
            "title": "[idle-ok] Wyrdheim — sync GDD consistency check",
            "branch": "gaming",
            "priority": "P2",
            "why": "Gardien canon / assets sans agency UE lourde",
        },
        {
            "title": "[idle-ok] Eve — BOM drift checklist",
            "branch": "robo",
            "priority": "P3",
            "why": "Surveillance hardware L0–L1 sans Pi",
        },
    ]


def promote_triage_to_tickets(
    *,
    item_id: str | None = None,
    project_id: str | None = None,
    dry_run: bool = False,
) -> dict[str, Any]:
    """Create Hub tickets from a product_triage deliverable (no LLM)."""
    from database.supabase_client import get_supabase

    deliverable = None
    if item_id:
        deliverable = get_deliverable(item_id)
    else:
        # latest product_triage
        for entry in list_deliverables(limit=50):
            if entry.get("kind") == "product_triage":
                deliverable = get_deliverable(str(entry["item_id"]))
                break

    tickets_src: list[dict[str, Any]] = []
    if deliverable:
        body = deliverable.get("body") or {}
        triage = body.get("triage") or {}
        raw = triage.get("tickets") if isinstance(triage, dict) else None
        if isinstance(raw, list):
            tickets_src = [t for t in raw if isinstance(t, dict)]

    if not tickets_src:
        tickets_src = offline_triage_tickets()
        source = "offline_fallback"
    else:
        source = "deliverable"

    # Resolve project_id — prefer explicit, else first open project, else skip insert
    pid = project_id
    db = get_supabase()
    if not pid:
        try:
            projects = db.select("projects", limit=1) or []
            if projects:
                pid = projects[0].get("id")
        except Exception:
            pid = None

    created: list[dict[str, Any]] = []
    skipped: list[str] = []
    for t in tickets_src[:8]:
        title = str(t.get("title") or "").strip()
        if not title:
            continue
        if not title.lower().startswith("[idle-ok]"):
            title = f"[idle-ok] {title}"
        priority_map = {"P1": "high", "P2": "medium", "P3": "low", "high": "high", "medium": "medium", "low": "low"}
        priority = priority_map.get(str(t.get("priority") or "P2"), "medium")
        desc = (
            f"Source: idle work ({source})\n"
            f"Branch: {t.get('branch', 'hub')}\n"
            f"Why: {t.get('why', '')}\n"
            "Label intent: idle-ok — exécutable sans brief CEO stratégique."
        )
        payload = {
            "project_id": pid,
            "type": "improvement",
            "priority": priority,
            "title": title[:200],
            "description": desc[:4000],
            "source": "quick_capture",
            "status": "open",
            "assignee_agent_id": None,
            "story_points": None,
            "due_date": None,
        }
        if dry_run or not pid:
            skipped.append(title)
            created.append({**payload, "dry_run": True, "missing_project": not pid})
            continue
        try:
            row = db.insert("tickets", payload)
            created.append(row if isinstance(row, dict) else payload)
        except Exception as exc:
            logger.warning("idle promote ticket failed: %s", exc)
            skipped.append(f"{title}: {exc}")

    return {
        "ok": True,
        "source": source,
        "project_id": pid,
        "created_count": sum(1 for c in created if not c.get("dry_run")),
        "tickets": created,
        "skipped": skipped,
        "item_id": item_id,
    }
