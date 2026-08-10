"""Security incident ingest — Résonance / apps → Hub alert + journal + email."""

from __future__ import annotations

import logging
import os
from typing import Any

logger = logging.getLogger(__name__)


def _severity_emoji(severity: str) -> str:
    return {
        "critical": "🛑",
        "high": "🚨",
        "medium": "⚠️",
        "low": "ℹ️",
    }.get((severity or "").lower(), "🚨")


def run_security_ingest(payload: dict[str, Any]) -> dict[str, Any]:
    """
    Accepts RESONANCE (or other app) security events.
    - Telegram / Discord via notify_hub
    - Email via Gmail Composio (CEO_GMAIL / SECURITY_ALERT_EMAIL)
    - Error journal → bug_watchdog / fix_pipeline when severity high+
    """
    from skills.skill_error_journal import log_error
    from skills.skill_hub_notify import notify_hub

    severity = str(payload.get("severity") or "high").lower()
    event_type = str(payload.get("type") or "unknown")
    title = str(payload.get("title") or "Security event")[:200]
    detail = str(payload.get("detail") or "")[:1500]
    source = str(payload.get("source") or "unknown")
    repo_slug = str(payload.get("repo_slug") or "resonance")
    environment = str(payload.get("environment") or "production")
    ip_hash = payload.get("ipHash") or payload.get("ip_hash")
    user_hash = payload.get("userIdHash") or payload.get("user_id_hash")

    emoji = _severity_emoji(severity)
    msg = (
        f"{emoji} SECURITY [{severity.upper()}]\n"
        f"source={source} repo={repo_slug} env={environment}\n"
        f"type={event_type}\n"
        f"{title}\n"
        f"{detail}\n"
        f"ip={ip_hash or '—'} user={user_hash or '—'}"
    )

    notifications = notify_hub(msg[:3500])

    email_to = (
        os.getenv("SECURITY_ALERT_EMAIL", "").strip()
        or os.getenv("CEO_GMAIL", "").strip()
    )
    email_ok = False
    if email_to and severity in ("high", "critical", "medium"):
        try:
            from services.secretary_composio import send_email

            result = send_email(
                email_to,
                f"[RESONANCE SECURITY] {severity.upper()} — {title[:80]}",
                msg,
                agent_id="system",
            )
            email_ok = bool(result.get("success"))
        except Exception as exc:
            logger.warning("security email failed: %s", exc)

    agent_name = "dev_resonance" if repo_slug == "resonance" else "qa_agent"
    journal_id = None
    if severity in ("high", "critical"):
        journal_id = log_error(
            agent_name=agent_name,
            error_type=f"security_{event_type}",
            error_message=title,
            context=msg[:1000],
            task_id=str(payload.get("at") or event_type)[:64],
        )

    return {
        "workflow": "security_ingest",
        "success": True,
        "action": "ingested",
        "severity": severity,
        "type": event_type,
        "repo_slug": repo_slug,
        "journal_id": journal_id,
        "notifications": notifications,
        "email": email_ok,
        "email_to": email_to if email_ok else None,
    }
