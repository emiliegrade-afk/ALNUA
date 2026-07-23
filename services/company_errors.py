"""Unified company error queue — local JSON + Supabase agent_error_journal.

CEO decides WHAT to build; ops/fixes run autonomously on this queue.
"""

from __future__ import annotations

import hashlib
import logging
import os
from typing import Any, Literal

logger = logging.getLogger(__name__)

Source = Literal["local", "supabase", "merged"]


def _dedupe_key(entry: dict[str, Any]) -> str:
    repo = entry.get("repo_slug") or ""
    etype = entry.get("error_type") or ""
    msg = (entry.get("error_message") or "")[:120]
    return hashlib.sha256(f"{repo}|{etype}|{msg}".encode()).hexdigest()[:16]


def _normalize_local(entry: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": entry.get("id"),
        "source": "local",
        "agent_name": entry.get("agent_name", "unknown"),
        "task_id": entry.get("task_id"),
        "repo_slug": entry.get("repo_slug"),
        "error_type": entry.get("error_type", "unknown"),
        "error_message": entry.get("error_message", ""),
        "status": entry.get("status", "open"),
        "created_at": entry.get("created_at"),
        "attempts": entry.get("attempts", 0),
        "dedupe_key": _dedupe_key(entry),
    }


def _normalize_supabase(row: dict[str, Any]) -> dict[str, Any]:
    ctx = row.get("context") or ""
    repo_slug = None
    if isinstance(ctx, str) and "repo_slug=" in ctx:
        for part in ctx.split():
            if part.startswith("repo_slug="):
                repo_slug = part.split("=", 1)[1]
    return {
        "id": row.get("id"),
        "source": "supabase",
        "agent_name": row.get("agent_name", "unknown"),
        "task_id": row.get("task_id"),
        "repo_slug": repo_slug,
        "error_type": row.get("error_type", "unknown"),
        "error_message": row.get("error_message", ""),
        "status": row.get("status", "open"),
        "created_at": row.get("created_at"),
        "attempts": int(row.get("attempts") or 0),
        "dedupe_key": _dedupe_key(
            {
                "repo_slug": repo_slug,
                "error_type": row.get("error_type"),
                "error_message": row.get("error_message"),
            }
        ),
    }


def _list_supabase_open(*, repo_slug: str | None, limit: int) -> list[dict[str, Any]]:
    try:
        from database.supabase_client import get_supabase

        db = get_supabase()
        q = (
            db.raw.table("agent_error_journal")
            .select(
                "id, agent_name, task_id, error_type, error_message, context, "
                "status, attempts, created_at"
            )
            .eq("status", "open")
            .order("created_at", desc=True)
            .limit(limit)
        )
        rows = q.execute().data or []
        items = [_normalize_supabase(r) for r in rows]
        if repo_slug:
            items = [e for e in items if e.get("repo_slug") == repo_slug or not e.get("repo_slug")]
        return items
    except Exception as exc:
        logger.debug("company_errors supabase list failed: %s", exc)
        return []


def record_company_error(
    *,
    agent_name: str,
    error_type: str,
    error_message: str,
    repo_slug: str | None = None,
    task_id: str | None = None,
    context: str | None = None,
    qa_errors: list[str] | None = None,
    status: str = "open",
    solution: str | None = None,
) -> dict[str, Any]:
    """Write to local journal + mirror open errors to Supabase when available."""
    from services.coding_error_journal import record_coding_error

    ctx = context or ""
    if repo_slug and "repo_slug=" not in ctx:
        ctx = f"repo_slug={repo_slug} {ctx}".strip()

    local = record_coding_error(
        agent_name=agent_name,
        task_id=task_id,
        repo_slug=repo_slug,
        error_type=error_type,
        error_message=error_message,
        qa_errors=qa_errors,
        status=status,
        solution=solution,
    )

    supabase_id = None
    if status == "open":
        try:
            from skills.skill_error_journal import log_error

            supabase_id = log_error(
                agent_name=agent_name,
                error_type=error_type,
                error_message=error_message,
                context=ctx[:1000] if ctx else None,
                task_id=task_id,
            )
        except Exception as exc:
            logger.debug("company_errors supabase record failed: %s", exc)

    return {"local": local, "supabase_id": supabase_id}


def list_open_errors(
    *,
    repo_slug: str | None = None,
    agent_name: str | None = None,
    limit: int = 50,
) -> list[dict[str, Any]]:
    """Merged open errors (Supabase primary, local JSON fills gaps)."""
    from services.coding_error_journal import load_journal

    by_key: dict[str, dict[str, Any]] = {}

    for row in _list_supabase_open(repo_slug=repo_slug, limit=limit * 2):
        by_key[row["dedupe_key"]] = row

    for entry in load_journal().get("entries", []):
        if entry.get("status") != "open":
            continue
        norm = _normalize_local(entry)
        if repo_slug and norm.get("repo_slug") != repo_slug:
            continue
        if agent_name and norm.get("agent_name") != agent_name:
            continue
        if norm["dedupe_key"] not in by_key:
            by_key[norm["dedupe_key"]] = norm

    items = list(by_key.values())
    items.sort(key=lambda e: e.get("created_at") or "", reverse=True)
    return items[:limit]


def count_open_errors(
    *,
    repo_slug: str | None = None,
    agent_name: str | None = None,
) -> int:
    return len(list_open_errors(repo_slug=repo_slug, agent_name=agent_name, limit=10_000))


def summarize_open_by_repo() -> list[dict[str, Any]]:
    """Per-repo open error counts for run_ops."""
    from services.app_registry import list_apps

    summary: list[dict[str, Any]] = []
    for app in list_apps(include_disabled=False):
        if app.slug == "hub":
            continue
        count = count_open_errors(repo_slug=app.slug)
        if count:
            summary.append(
                {
                    "slug": app.slug,
                    "name": app.name,
                    "branch": app.branch,
                    "open_count": count,
                    "errors": list_open_errors(repo_slug=app.slug, limit=3),
                }
            )
    hub_count = count_open_errors(repo_slug="hub")
    if hub_count:
        summary.insert(
            0,
            {
                "slug": "hub",
                "name": "ALNUA Hub",
                "branch": "hub",
                "open_count": hub_count,
                "errors": list_open_errors(repo_slug="hub", limit=3),
            },
        )
    return summary


def auto_create_fix_issues(
    *,
    max_issues: int = 5,
    min_open_per_repo: int = 1,
) -> dict[str, Any]:
    """Create GitHub agent-ready issues for repos with open errors (autonomous ops)."""
    if not os.getenv("GITHUB_TOKEN", "").strip():
        return {"success": False, "error": "GITHUB_TOKEN absent", "created": []}

    from config.github_repos import get_target_by_slug
    from skills.skill_gh_issues import create_github_issue

    created: list[dict[str, Any]] = []
    for block in summarize_open_by_repo():
        if len(created) >= max_issues:
            break
        slug = block["slug"]
        if block["open_count"] < min_open_per_repo:
            continue
        target = get_target_by_slug(slug)
        if not target or not target.github_repo:
            continue

        sample = block.get("errors") or []
        lines = [
            f"**Ops automatique ALNUA** — {block['open_count']} erreur(s) ouverte(s) sur `{slug}`.",
            "",
            "Le pipeline coding doit corriger sans intervention CEO (decision produit déjà validée).",
            "",
        ]
        for err in sample[:3]:
            lines.append(
                f"- [{err.get('error_type')}] {(err.get('error_message') or '')[:200]}"
            )

        title = f"[Auto-fix ops] {slug} — {block['open_count']} erreur(s) ouverte(s)"
        try:
            raw = create_github_issue(
                title=title[:120],
                body="\n".join(lines),
                repo_slug=slug,
                labels="agent-ready,auto-ops",
            )
            if "Issue #" in raw:
                num_part = raw.split("Issue #")[1].split()[0]
                created.append({"slug": slug, "issue_number": int(num_part), "raw": raw[:200]})
        except Exception as exc:
            logger.warning("auto_create_fix_issues %s failed: %s", slug, exc)

    return {"success": True, "created": created, "count": len(created)}
