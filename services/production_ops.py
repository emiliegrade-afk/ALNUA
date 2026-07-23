"""Production ops orchestrator — Sentry ingest + status (Phase 4)."""

from __future__ import annotations

import logging
from typing import Any

from services.sentry_ops import (
    SentryIngestEvent,
    _load_dedup,
    ingest_sentry_event,
    parse_sentry_webhook,
    verify_sentry_signature,
)
from skills.skill_error_journal import get_open_errors_summary

logger = logging.getLogger(__name__)


def run_sentry_webhook(
    payload: dict[str, Any],
    *,
    body: bytes = b"",
    signature: str | None = None,
    secret: str = "",
    create_issue: bool = True,
    allow_unsigned: bool = False,
    trusted_relay: bool = False,
) -> dict[str, Any]:
    """Verify signature, parse payload, ingest."""
    if not trusted_relay and not verify_sentry_signature(
        body,
        signature,
        secret,
        allow_unsigned=allow_unsigned,
    ):
        return {"success": False, "error": "invalid_signature"}

    event = parse_sentry_webhook(payload)
    if not event:
        return {
            "success": True,
            "action": "ignored",
            "reason": "non-actionable or resolved event",
        }

    result = ingest_sentry_event(event, create_issue=create_issue)
    return {"success": True, **result}


def simulate_sentry_event(
    *,
    title: str,
    message: str = "",
    project_slug: str = "hub",
    level: str = "error",
    dry_run: bool = False,
) -> dict[str, Any]:
    """Dev/test helper — inject a synthetic Sentry event."""
    import hashlib

    fingerprint = hashlib.sha256(f"{project_slug}|{title}".encode()).hexdigest()[:24]
    event = SentryIngestEvent(
        fingerprint=fingerprint,
        title=title,
        message=message or title,
        level=level,
        project_slug=project_slug,
        culprit="app/screens/Home.tsx",
        environment="staging",
        stacktrace="TypeError: Cannot read property 'map' of undefined",
    )
    if dry_run:
        return {"success": True, "action": "dry_run", "event": event.model_dump()}
    return {"success": True, **ingest_sentry_event(event)}


def get_production_ops_status() -> dict[str, Any]:
    """Cockpit data: Sentry dedup + open errors + pipeline hints."""
    dedup = _load_dedup()
    fingerprints = dedup.get("fingerprints") or {}
    recent = dedup.get("recent") or []

    sentry_open = sum(
        1
        for _fp, meta in fingerprints.items()
        if meta.get("journal_id") and not meta.get("resolved")
    )

    errors_summary = get_open_errors_summary()
    open_lines = [
        ln
        for ln in errors_summary.splitlines()
        if ln.strip() and not ln.startswith("[OK]")
    ]

    return {
        "sentry": {
            "tracked_fingerprints": len(fingerprints),
            "open_count": sentry_open,
            "recent_ingests": recent[:10],
            "auto_issue": True,
        },
        "error_journal": {
            "open_count": len(open_lines),
            "summary": errors_summary,
        },
        "pipeline": {
            "bug_watchdog": "active",
            "poll_issues_loop": "active_if_github_configured",
        },
        "webhook_url": "/webhook/sentry",
    }
