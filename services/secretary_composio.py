"""Composio bridge for Nadia — Gmail + Google Calendar (OAuth via /connect)."""

from __future__ import annotations

import logging
import os
from datetime import datetime, timedelta
from typing import Any
from zoneinfo import ZoneInfo

from config.settings import get_settings

logger = logging.getLogger(__name__)
_PARIS = ZoneInfo("Europe/Paris")


def composio_user_id() -> str:
    """Shared OAuth identity for CEO tools (Gmail, Calendar)."""
    settings = get_settings()
    return (
        settings.composio_user_id.strip()
        or os.getenv("COMPOSIO_USER_ID", "").strip()
        or os.getenv("COMPOSIO_CEO_USER_ID", "").strip()
        or "alnua_coo"
    )


def expected_ceo_gmail() -> str:
    """Gmail account Emilie wants Nadia to use (default: alnua.global@gmail.com)."""
    return get_settings().ceo_gmail.strip().lower()


def connected_gmail_email() -> str | None:
    from skills.skill_composio import get_gmail_profile_email

    email = get_gmail_profile_email(composio_user_id())
    return email.lower() if email else None


def gmail_account_ok() -> bool:
    expected = expected_ceo_gmail()
    if not expected:
        return is_connected("gmail")
    current = connected_gmail_email()
    return bool(current and current == expected)


def _gmail_connect_instructions() -> str:
    expected = expected_ceo_gmail()
    if expected:
        return f"Connecte-toi avec **{expected}** (compte ALNUA)."
    return "Ouvre le lien et autorise l'accès Google."


def get_oauth_link_for_ceo(app: str, *, force_reconnect: bool = False) -> str:
    from skills.skill_composio import disconnect_toolkit, get_oauth_link

    toolkit = app.upper()
    uid = composio_user_id()

    if toolkit == "GMAIL" and force_reconnect:
        disconnect_toolkit(uid, "gmail")

    link = get_oauth_link(app=toolkit, user_id=uid)

    if link.startswith("Erreur") or "déjà connecté" in link.lower() or "deja connecte" in link.lower():
        if toolkit == "GMAIL" and is_connected("gmail"):
            current = connected_gmail_email()
            expected = expected_ceo_gmail()
            if expected and current and current != expected:
                disconnect_toolkit(uid, "gmail")
                link = get_oauth_link(app=toolkit, user_id=uid)
                if link.startswith("http"):
                    return (
                        f"⚠️ Gmail actuel : {current}\n"
                        f"Compte attendu : {expected}\n\n"
                        f"🔗 Reconnexion — {_gmail_connect_instructions()}\n{link}"
                    )
        return link

    if toolkit == "GMAIL" and link.startswith("http"):
        return f"🔗 {_gmail_connect_instructions()}\n{link}"

    return link


def list_ceo_connections() -> list[dict[str, Any]]:
    from skills.skill_composio import list_connected_apps

    return list_connected_apps(user_id=composio_user_id())


def is_connected(toolkit: str) -> bool:
    from skills.skill_composio import has_active_connection

    return has_active_connection(composio_user_id(), toolkit.lower())


def connection_status_text() -> str:
    apps = list_ceo_connections()
    expected = expected_ceo_gmail()
    gmail_email = connected_gmail_email()

    if not apps:
        hint = f"\nCompte Gmail à utiliser : {expected}" if expected else ""
        return (
            "Aucune app connectée.\n"
            "• Telegram : `/connect gmail` puis `/connect calendar`"
            f"{hint}"
        )
    lines = ["Apps connectées :"]
    for row in apps:
        app = row.get("app", "?")
        extra = ""
        if app == "GMAIL" and gmail_email:
            extra = f" ({gmail_email})"
            if expected and gmail_email != expected:
                extra += " ⚠️ mauvais compte — `/connect gmail` pour reconnecter"
        lines.append(f"• {app}{extra} — {row.get('status', '?')}")
    if not is_connected("gmail"):
        lines.append(f"\n⚠️ Gmail non connecté — `/connect gmail` ({expected or 'Google'})")
    elif expected and gmail_email and gmail_email != expected:
        lines.append(f"\n⚠️ Attendu : {expected} — envoie `/connect gmail` pour changer.")
    if not is_connected("googlecalendar"):
        lines.append("⚠️ Calendar non connecté — `/connect calendar`")
    return "\n".join(lines)


def _execute(action: str, params: dict[str, Any]) -> dict[str, Any]:
    from skills.skill_composio import composio_execute

    if not os.getenv("COMPOSIO_API_KEY", "").strip():
        return {"success": False, "error": "COMPOSIO_API_KEY manquante dans .env"}
    return composio_execute(action, params, user_id=composio_user_id())


def send_email(to: str, subject: str, body: str) -> dict[str, Any]:
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
    return _execute(
        "GMAIL_SEND_EMAIL",
        {"recipient_email": to, "subject": subject, "body": body},
    )


def fetch_inbox_emails(*, max_results: int = 8) -> list[dict[str, str]]:
    """Return simplified inbox rows for triage."""
    if not is_connected("gmail"):
        return []

    result = _execute(
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


def fetch_calendar_events(*, days_ahead: int = 2) -> list[dict[str, str]]:
    if not is_connected("googlecalendar"):
        return []

    now = datetime.now(_PARIS)
    time_min = now.isoformat()
    time_max = (now + timedelta(days=days_ahead)).isoformat()

    for action, params in (
        (
            "GOOGLECALENDAR_FIND_EVENT",
            {"time_min": time_min, "time_max": time_max, "max_results": 12},
        ),
        (
            "GOOGLECALENDAR_EVENTS_LIST",
            {
                "time_min": time_min,
                "time_max": time_max,
                "max_results": 12,
                "calendar_id": "primary",
            },
        ),
    ):
        result = _execute(action, params)
        if not result.get("success"):
            continue
        data = result.get("data") or {}
        if isinstance(data, dict) and "data" in data:
            data = data["data"]
        items = []
        if isinstance(data, dict):
            items = data.get("items") or data.get("events") or []
        elif isinstance(data, list):
            items = data
        events: list[dict[str, str]] = []
        for ev in items:
            if not isinstance(ev, dict):
                continue
            start = ev.get("start") or {}
            when = start.get("dateTime") or start.get("date") or "?"
            events.append(
                {
                    "title": str(ev.get("summary") or ev.get("title") or "Sans titre")[:120],
                    "when": str(when),
                    "location": str(ev.get("location") or "")[:80],
                }
            )
        if events:
            return events
    return []


def create_calendar_event(
    title: str,
    start_datetime: str,
    *,
    description: str = "",
    duration_minutes: int = 60,
) -> dict[str, Any]:
    if not is_connected("googlecalendar"):
        return {
            "success": False,
            "error": "Google Calendar non connecté — /connect googlecalendar",
        }
    return _execute(
        "GOOGLECALENDAR_CREATE_EVENT",
        {
            "summary": title,
            "start_datetime": start_datetime,
            "description": description,
            "event_duration_minutes": duration_minutes,
        },
    )
