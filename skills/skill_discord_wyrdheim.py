"""
skill_discord_wyrdheim.py — Gestion Discord Wyrdheim via Discord Bot

Variables d'env :
- DISCORD_BOT_TOKEN : token du bot Discord Wyrdheim
- DISCORD_GUILD_ID : ID du serveur Discord Wyrdheim

Channels mappés (configurer dans .env) :
- DISCORD_CHANNEL_ANNOUNCEMENTS (alias anglais) ou DISCORD_CHANNEL_ANNONCES
- DISCORD_CHANNEL_LORE
- DISCORD_CHANNEL_GENERAL
- DISCORD_CHANNEL_DEVLOG
"""

from __future__ import annotations

import logging
import os
from typing import Any

import httpx

logger = logging.getLogger(__name__)

DISCORD_API = "https://discord.com/api/v10"
DISCORD_NOT_CONFIGURED = (
    "Discord non configuré — renseigne DISCORD_BOT_TOKEN et les DISCORD_CHANNEL_* dans .env"
)


def discord_is_configured() -> bool:
    """True when the Wyrdheim bot token is set."""
    return bool(os.getenv("DISCORD_BOT_TOKEN", "").strip())


def get_headers() -> dict[str, str]:
    token = os.getenv("DISCORD_BOT_TOKEN", "").strip()
    if not token:
        raise ValueError(DISCORD_NOT_CONFIGURED)
    return {"Authorization": f"Bot {token}"}


def _announcements_channel_id() -> str | None:
    return os.getenv("DISCORD_CHANNEL_ANNOUNCEMENTS") or os.getenv("DISCORD_CHANNEL_ANNONCES")


def get_channel_id(channel_name: str) -> str | None:
    """Résout le nom d'un channel en ID Discord."""
    announcements = _announcements_channel_id()
    mapping = {
        "annonces": announcements,
        "announcements": announcements,
        "lore": os.getenv("DISCORD_CHANNEL_LORE"),
        "général": os.getenv("DISCORD_CHANNEL_GENERAL"),
        "dev-log": os.getenv("DISCORD_CHANNEL_DEVLOG"),
        "general": os.getenv("DISCORD_CHANNEL_GENERAL"),
        "game-design": os.getenv("DISCORD_CHANNEL_LORE"),
        "evenements": announcements,
        "support": os.getenv("DISCORD_CHANNEL_GENERAL"),
    }
    return mapping.get(channel_name.lower(), os.getenv("DISCORD_CHANNEL_GENERAL"))


def post_to_discord(channel: str, content: str, embed: bool = False, image_url: str = "") -> dict[str, Any]:
    """Poste un message dans un channel Discord."""
    if not discord_is_configured():
        return {"success": False, "error": DISCORD_NOT_CONFIGURED}

    channel_id = get_channel_id(channel)
    if not channel_id:
        return {
            "success": False,
            "error": f"Channel '{channel}' non configuré — renseigne DISCORD_CHANNEL_ANNOUNCEMENTS dans .env",
        }

    payload: dict[str, Any] = {"content": content}
    if embed:
        embed_body: dict[str, Any] = {
            "description": content,
            "color": 0x5E7E39,  # Vert Wyrdheim
        }
        if image_url:
            embed_body["image"] = {"url": image_url}
        payload = {"embeds": [embed_body]}

    try:
        with httpx.Client() as client:
            resp = client.post(
                f"{DISCORD_API}/channels/{channel_id}/messages",
                headers=get_headers(),
                json=payload,
            )
            resp.raise_for_status()
            data = resp.json()
            return {"success": True, "data": data}
    except Exception as exc:
        logger.warning("Discord post failed: %s", exc)
        return {"success": False, "error": str(exc)}


def get_recent_messages(channel: str, limit: int = 20) -> list[dict[str, str]]:
    """Lit les derniers messages d'un channel."""
    if not discord_is_configured():
        return []

    channel_id = get_channel_id(channel)
    if not channel_id:
        return []

    try:
        with httpx.Client() as client:
            resp = client.get(
                f"{DISCORD_API}/channels/{channel_id}/messages",
                headers=get_headers(),
                params={"limit": min(limit, 100)},
            )
            resp.raise_for_status()
            messages = resp.json()
            return [
                {"author": m["author"]["username"], "content": m["content"]}
                for m in messages
            ]
    except Exception as exc:
        logger.warning("Discord read failed: %s", exc)
        return []
