"""Full Sentry event ingest — dedup, journal, optional GitHub hotfix."""

from __future__ import annotations

import logging
import os
from datetime import datetime, timezone
from typing import Any

from services.sentry_ops_dedup import load_dedup, save_dedup
from services.sentry_ops_parse import SentryIngestEvent
from services.sentry_ops_resolve import resolve_agent_from_sentry, resolve_repo_slug_from_sentry

logger = logging.getLogger(__name__)


def ingest_sentry_event(
    event: SentryIngestEvent,
    *,
    create_issue: bool = True,
    dedup_hours: int = 24,
) -> dict[str, Any]:
    """
    Full ingest: dedup → error journal → optional GitHub hotfix issue.
    bug_watchdog picks up journal entries automatically.
    """
    import services.sentry_ops as sentry_ops

    dedup = load_dedup()
    fingerprints = dedup.setdefault("fingerprints", {})
    existing = fingerprints.get(event.fingerprint)

    now = datetime.now(timezone.utc)
    if existing:
        last_seen = existing.get("last_seen", "")
        try:
            last_dt = datetime.fromisoformat(last_seen.replace("Z", "+00:00"))
            age_h = (now - last_dt).total_seconds() / 3600
        except ValueError:
            age_h = dedup_hours + 1
        existing["count"] = int(existing.get("count") or 0) + 1
        existing["last_seen"] = now.isoformat()
        save_dedup(dedup)
        if age_h < dedup_hours:
            return {
                "action": "dedup_skipped",
                "fingerprint": event.fingerprint,
                "occurrences": existing["count"],
                "github_issue": existing.get("github_issue"),
                "journal_id": existing.get("journal_id"),
            }

    repo_slug = resolve_repo_slug_from_sentry(event)
    agent_name = resolve_agent_from_sentry(event, repo_slug)

    context_parts = [
        f"Sentry {event.level} — {event.environment}",
        f"project={event.project_slug}",
        f"culprit={event.culprit}",
        f"fingerprint={event.fingerprint}",
    ]
    if event.permalink:
        context_parts.append(f"url={event.permalink}")
    if event.stacktrace:
        context_parts.append(f"stack:\n{event.stacktrace[:1500]}")

    journal_id = sentry_ops.log_error(
        agent_name=agent_name,
        error_type=f"sentry_{event.level}",
        error_message=event.message or event.title,
        context="\n".join(context_parts),
        task_id=event.issue_id or event.event_id or event.fingerprint,
    )

    github_issue: dict[str, Any] | None = None
    if create_issue and os.getenv("SENTRY_AUTO_ISSUE", "true").lower() in ("1", "true", "yes"):
        try:
            github_issue = sentry_ops.create_hotfix_github_issue(
                event,
                repo_slug=repo_slug,
                journal_id=journal_id,
                mark_agent_ready=event.level in ("error", "fatal", "critical"),
            )
        except Exception as exc:
            logger.warning("sentry hotfix issue failed: %s", exc)

    fingerprints[event.fingerprint] = {
        "last_seen": now.isoformat(),
        "first_seen": (existing or {}).get("first_seen") or now.isoformat(),
        "count": 1 if not existing else int(existing.get("count") or 0),
        "title": event.title,
        "journal_id": journal_id,
        "github_issue": github_issue,
        "repo_slug": repo_slug,
    }
    recent = dedup.setdefault("recent", [])
    recent.insert(
        0,
        {
            "fingerprint": event.fingerprint,
            "title": event.title,
            "at": now.isoformat(),
            "journal_id": journal_id,
            "issue_number": (github_issue or {}).get("number"),
        },
    )
    dedup["recent"] = recent[:50]
    save_dedup(dedup)

    return {
        "action": "ingested",
        "fingerprint": event.fingerprint,
        "journal_id": journal_id,
        "agent_name": agent_name,
        "repo_slug": repo_slug,
        "github_issue": github_issue,
    }
