"""Composio bridge for Nadia — Gmail + Google Calendar (OAuth via /connect)."""

from __future__ import annotations

from services.secretary_composio_calendar import (  # noqa: F401 — re-export
    create_calendar_event,
    fetch_calendar_events,
    fetch_calendar_events_raw,
    update_calendar_event,
)
from services.secretary_composio_gmail import fetch_inbox_emails, send_email  # noqa: F401 — re-export
from services.secretary_composio_oauth import (  # noqa: F401 — re-export
    composio_user_id,
    connected_gmail_email,
    connection_status_text,
    expected_ceo_gmail,
    get_oauth_link_for_ceo,
    gmail_account_ok,
    split_oauth_reply,
    is_connected,
    list_ceo_connections,
)
