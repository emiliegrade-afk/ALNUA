"""
skill_steam.py — Statistiques Steam publiques pour Wyrdheim (Phase 18, ROADMAP.md)

Variables d'env :
- STEAM_API_KEY : clé Steam Web API (steamcommunity.com/dev/apikey)
- STEAM_APP_ID  : App ID Steamworks de Wyrdheim

Limite connue et assumée : Valve n'expose aucune API publique pour le nombre
de wishlists — cette donnée n'existe que dans le dashboard Steamworks Partner
(accès partenaire, pas une simple clé Web API). `get_wishlist_count()` renvoie
donc toujours `None`, documenté explicitement plutôt que deviné. Seul le
nombre de joueurs simultanés (`GetNumberOfCurrentPlayers`, public, sans clé)
est réellement branché.
"""

from __future__ import annotations

import logging
import os

import httpx

logger = logging.getLogger(__name__)

STEAM_API = "https://api.steampowered.com"


def steam_is_configured() -> bool:
    """True quand un App ID Steam est renseigné (le seul prérequis réel — l'endpoint est public)."""
    return bool(os.getenv("STEAM_APP_ID", "").strip())


def get_concurrent_players() -> int | None:
    """Nombre de joueurs simultanés — endpoint public, aucune clé requise."""
    app_id = os.getenv("STEAM_APP_ID", "").strip()
    if not app_id:
        return None
    try:
        with httpx.Client(timeout=10) as client:
            resp = client.get(
                f"{STEAM_API}/ISteamUserStats/GetNumberOfCurrentPlayers/v1/",
                params={"appid": app_id},
            )
            resp.raise_for_status()
            return resp.json().get("response", {}).get("player_count")
    except Exception as exc:
        logger.warning("[Steam] GetNumberOfCurrentPlayers failed: %s", exc)
        return None


def get_wishlist_count() -> None:
    """Toujours None — voir la note de module. Gardé comme point d'extension
    explicite si un accès Steamworks Partner devient disponible un jour."""
    return None
