"""
skill_naia_embodied.py — Interface avec la Edge Function naia-embodied

Actions disponibles :
- speak : faire parler Eve (TTS)
- move : déplacer un servomoteur
- look : orienter la tête/caméra
- gesture : exécuter un geste prédéfini
- status : état du robot (batterie, température, connexion)
"""

from __future__ import annotations

import os
from typing import Any

import httpx


def call_naia_embodied(action: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
    """
    Appelle la Edge Function naia-embodied sur Supabase.

    Returns:
        {"status_code": int, "body": str, "success": bool}
    """
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_KEY")

    if not supabase_url:
        return {
            "success": False,
            "status_code": 0,
            "body": "SUPABASE_URL non configuré",
        }

    edge_url = f"{supabase_url}/functions/v1/naia-embodied"
    payload = {"action": action, "params": params or {}}

    try:
        resp = httpx.post(
            edge_url,
            headers={"Authorization": f"Bearer {supabase_key}"},
            json=payload,
            timeout=10,
        )
        return {
            "success": resp.status_code < 400,
            "status_code": resp.status_code,
            "body": resp.text[:500],
        }
    except Exception as e:
        return {
            "success": False,
            "status_code": 0,
            "body": str(e),
        }
