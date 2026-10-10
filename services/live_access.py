"""Nadia Live — what the voice session can actually reach (web, Gmail, socials)."""

from __future__ import annotations

import os
from typing import Any

import httpx

INTERNET_URL = "https://example.com"
HTTP_TIMEOUT_SECONDS = 8.0
CEO_APPS = ("gmail", "googlecalendar", "discord", "instagram", "linkedin")
CONNECTABLE_APPS = frozenset(CEO_APPS)


def probe_internet() -> dict[str, Any]:
    """A real outbound GET — proves the Hub machine can leave the LAN."""
    try:
        with httpx.Client(timeout=HTTP_TIMEOUT_SECONDS, follow_redirects=True) as client:
            response = client.get(INTERNET_URL)
        return {"ok": 200 <= response.status_code < 400, "detail": f"HTTP {response.status_code}"}
    except httpx.RequestError as exc:
        return {"ok": False, "detail": type(exc).__name__}


def _composio_app(name: str) -> dict[str, Any]:
    from services.secretary_composio import is_connected

    try:
        on = is_connected(name)
        extra: dict[str, Any] = {}
        if name == "gmail":
            from services.secretary_composio import (
                connected_gmail_email,
                expected_ceo_gmail,
                gmail_account_ok,
            )

            extra["account"] = connected_gmail_email()
            extra["expected"] = expected_ceo_gmail()
            extra["account_ok"] = gmail_account_ok()
        return {"ok": on, "via": "composio", **extra}
    except Exception as exc:
        return {"ok": False, "via": "composio", "detail": type(exc).__name__}


def probe_access() -> dict[str, Any]:
    """Snapshot for the cockpit. Never includes tokens or OAuth secrets."""
    internet = probe_internet()
    apps = {name: _composio_app(name) for name in CEO_APPS}
    discord_bot = bool(os.getenv("DISCORD_BOT_TOKEN", "").strip())
    if discord_bot and not apps["discord"]["ok"]:
        apps["discord"] = {
            "ok": True,
            "via": "bot",
            "detail": "Bot Wyrdheim (annonces), pas tes messages privés.",
        }
    return {
        "internet": internet,
        "apps": apps,
        "ready": {
            "research": internet["ok"],
            "mail": bool(apps["gmail"]["ok"]),
            "calendar": bool(apps["googlecalendar"]["ok"]),
            "discord": bool(apps["discord"]["ok"]),
            "instagram": bool(apps["instagram"]["ok"]),
            "linkedin": bool(apps["linkedin"]["ok"]),
        },
    }
