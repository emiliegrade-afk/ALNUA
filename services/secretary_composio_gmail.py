"""Gmail actions via Composio for Nadia."""

from __future__ import annotations

import logging
import os
from typing import Any

from services.secretary_composio_oauth import (
    composio_user_id,
    connected_gmail_email,
    expected_ceo_gmail,
    gmail_account_ok,
    is_connected,
)

logger = logging.getLogger(__name__)


def execute(action: str, params: dict[str, Any]) -> dict[str, Any]:
    from skills.skill_composio import composio_execute

    if not os.getenv("COMPOSIO_API_KEY", "").strip():
        return {"success": False, "error": "COMPOSIO_API_KEY manquante dans .env"}
    return composio_execute(action, params, user_id=composio_user_id())


def send_email(
    to: str,
    subject: str,
    body: str,
    *,
    agent_id: str = "secretary",
) -> dict[str, Any]:
    try:
        from services.permission_guard import PermissionDeniedError, require_capability

        require_capability(
            agent_id,
            "mail:send",
            resource=f"to:{(to or '')[:80]}",
            meta={"subject": (subject or "")[:80]},
        )
    except PermissionDeniedError as exc:
        return {"success": False, "error": str(exc)}
    except Exception:
        pass

    if not is_connected("gmail"):
        return {
            "success": False,
            "error": "Gmail non connecté — utilise /connect gmail sur Telegram Nadia.",
        }
    if not gmail_account_ok():
        expected = expected_ceo_gmail()
        current = connected_gmail_email() or "?"
        return {
            "success": False,
            "error": (
                f"Mauvais compte Gmail ({current}). "
                f"Reconnecte avec {expected} via /connect gmail."
            ),
        }
    return execute(
        "GMAIL_SEND_EMAIL",
        {"recipient_email": to, "subject": subject, "body": body},
    )


def fetch_inbox_emails(*, max_results: int = 8) -> list[dict[str, str]]:
    """Return simplified inbox rows for triage."""
    if not is_connected("gmail"):
        return []

    result = execute(
        "GMAIL_FETCH_EMAILS",
        {
            "max_results": max_results,
            "label_ids": ["INBOX"],
            "verbose": True,
        },
    )
    if not result.get("success"):
        logger.warning("GMAIL_FETCH_EMAILS failed: %s", result.get("error"))
        return []

    data = result.get("data") or {}
    if isinstance(data, dict) and "data" in data:
        data = data["data"]

    raw_messages = []
    if isinstance(data, dict):
        raw_messages = data.get("messages") or data.get("emails") or []
    elif isinstance(data, list):
        raw_messages = data

    emails: list[dict[str, str]] = []
    for msg in raw_messages:
        if not isinstance(msg, dict):
            continue
        subject = (
            msg.get("subject")
            or msg.get("Subject")
            or (msg.get("payload") or {}).get("headers", [{}])[0].get("value", "")
            if isinstance(msg.get("payload"), dict)
            else ""
        )
        sender = msg.get("from") or msg.get("sender") or msg.get("From") or "?"
        snippet = (msg.get("snippet") or msg.get("body") or msg.get("preview") or "")[:280]
        emails.append(
            {
                "from": str(sender)[:120],
                "subject": str(subject)[:200] or "(sans objet)",
                "body": snippet,
            }
        )
    return emails
