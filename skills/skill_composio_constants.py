"""Composio app mappings per ALNUA agent role."""

from __future__ import annotations

AGENT_APP_MAP: dict[str, list[str]] = {
    "coo_agent": [
        "GMAIL", "GOOGLECALENDAR", "NOTION", "SLACK",
        "GITHUB", "GOOGLESHEETS",
    ],
    "pm_agent": [
        "GITHUB", "NOTION", "GOOGLESHEETS", "LINEAR",
    ],
    "dev_app_agent": [
        "GITHUB", "VERCEL", "SUPABASE",
    ],
    "marketing_agent": [
        "NOTION", "GOOGLEDRIVE", "GITHUB", "GOOGLESHEETS",
    ],
    "content_agent": [
        "NOTION", "GOOGLEDOCS", "GITHUB",
    ],
    "qa_agent": [
        "GITHUB", "SLACK",
    ],
    "hardware_agent": [
        "NOTION", "GOOGLEDRIVE",
    ],
    "game_director_agent": [
        "DISCORD", "NOTION",
    ],
    "secretary_agent": [
        "GMAIL", "GOOGLECALENDAR", "NOTION", "DISCORD", "INSTAGRAM", "LINKEDIN",
    ],
    "spec_agent": [
        "NOTION", "GOOGLEDOCS", "GITHUB",
    ],
}

_STALE_CONNECTION_STATUSES = frozenset(
    {"EXPIRED", "FAILED", "REVOKED", "INITIALIZING", "INITIATED"},
)
