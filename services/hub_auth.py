"""Hub API authentication — scoped keys and optional IP allowlist."""

from __future__ import annotations

import secrets

from config.settings import get_settings


def valid_hub_api_keys() -> list[str]:
    """Master HUB_API_KEY plus any non-empty scoped channel keys."""
    settings = get_settings()
    keys: list[str] = []
    seen: set[str] = set()
    for raw in (
        settings.hub_api_key,
        settings.hub_api_key_web,
        settings.hub_api_key_n8n,
        settings.hub_api_key_mcp,
        settings.hub_api_key_cursor,
    ):
        key = (raw or "").strip()
        if key and key not in seen:
            seen.add(key)
            keys.append(key)
    return keys


def hub_api_key_valid(provided: str | None) -> bool:
    """Constant-time compare against master or any scoped channel key."""
    if not provided:
        return False
    for expected in valid_hub_api_keys():
        if secrets.compare_digest(provided, expected):
            return True
    return False


def client_ip_allowed(client_ip: str | None) -> bool:
    """When HUB_IP_ALLOWLIST is empty, all IPs pass; else exact match only."""
    allowlist = (get_settings().hub_ip_allowlist or "").strip()
    if not allowlist:
        return True
    if not client_ip:
        return False
    allowed = {ip.strip() for ip in allowlist.split(",") if ip.strip()}
    return client_ip.strip() in allowed
