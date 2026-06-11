"""
skill_discord_wyrdheim.py — Gestion Discord Wyrdheim via Discord Bot

Variables d'env :
- DISCORD_BOT_TOKEN : token du bot Discord Wyrdheim
- DISCORD_GUILD_ID : ID du serveur Discord Wyrdheim

Channels mappés (configurer dans .env) :
- DISCORD_CHANNEL_ANNONCES
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


def get_headers() -> dict[str, str]:
    token = os.getenv("DISCORD_BOT_TOKEN")
    if not token:
        raise ValueError("DISCORD_BOT_TOKEN non configuré dans .env")
    return {"Authorization": f"Bot {token}"}


def get_channel_id(channel_name: str) -> str | None:
    """Résout le nom d'un channel en ID Discord."""
    mapping = {
        "annonces": os.getenv("DISCORD_CHANNEL_ANNONCES"),
        "lore": os.getenv("DISCORD_CHANNEL_LORE"),
        "général": os.getenv("DISCORD_CHANNEL_GENERAL"),
        "dev-log": os.getenv("DISCORD_CHANNEL_DEVLOG"),
        "general": os.getenv("DISCORD_CHANNEL_GENERAL"),
        "game-design": os.getenv("DISCORD_CHANNEL_LORE"),
        "evenements": os.getenv("DISCORD_CHANNEL_ANNONCES"),
        "support": os.getenv("DISCORD_CHANNEL_GENERAL"),
    }
    return mapping.get(channel_name.lower(), os.getenv("DISCORD_CHANNEL_GENERAL"))


def post_to_discord(channel: str, content: str, embed: bool = False) -> dict[str, Any]:
    """Poste un message dans un channel Discord."""
    channel_id = get_channel_id(channel)
    if not channel_id:
        raise ValueError(f"Channel '{channel}' non configuré dans .env")

    payload: dict[str, Any] = {"content": content}
    if embed:
        payload = {
            "embeds": [
                {
                    "description": content,
                    "color": 0x5E7E39,  # Vert Wyrdheim
                }
            ]
        }

    with httpx.Client() as client:
        resp = client.post(
            f"{DISCORD_API}/channels/{channel_id}/messages",
            headers=get_headers(),
            json=payload,
        )
        resp.raise_for_status()
        return resp.json()


def get_recent_messages(channel: str, limit: int = 20) -> list[dict[str, str]]:
    """Lit les derniers messages d'un channel."""
    channel_id = get_channel_id(channel)
    if not channel_id:
        return []

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
