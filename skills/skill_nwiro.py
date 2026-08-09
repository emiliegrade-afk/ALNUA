"""
skill_nwiro.py — Client MCP pour le plugin Nwiro (UE5) — LEGACY (DEC-017).

Do not add new Gaming flows here. Target bridge = UE5.8 server + Hub skill.
This module remains until probes/callers migrate.

Nwiro expose un serveur MCP natif à http://localhost:5353/mcp
(UE5 + plugin Fab). Variables : NWIRO_HOST, NWIRO_PORT (défaut 5353).
Doc : https://docs.nwiro.ai
"""

from __future__ import annotations

import logging
import os
from typing import Any

import httpx

logger = logging.getLogger(__name__)

UE5_NOT_CONNECTED = (
    "UE5 non connecté — ouvre Unreal Engine avec le plugin Nwiro (port 5353)."
)


def get_nwiro_url() -> str:
    host = os.getenv("NWIRO_HOST", "localhost")
    port = os.getenv("NWIRO_PORT", "5353")
    return f"http://{host}:{port}/mcp"


def nwiro_is_available() -> bool:
    """Vérifie que le serveur Nwiro est accessible (UE5 ouvert avec plugin)."""
    try:
        host = os.getenv("NWIRO_HOST", "localhost")
        port = os.getenv("NWIRO_PORT", "5353")
        with httpx.Client(timeout=2) as client:
            resp = client.get(f"http://{host}:{port}/health")
            return resp.status_code == 200
    except Exception as exc:
        logger.debug("[Nwiro] Health check failed: %s", exc)
        return False


def nwiro_list_tools() -> list[dict[str, Any]]:
    """
    Liste tous les outils MCP disponibles dans Nwiro.
    Retourne [{"name": "blueprint_create_actor", "description": "...", "inputSchema": {...}}, ...]
    """
    if not nwiro_is_available():
        logger.debug("[Nwiro] tools/list skipped — %s", UE5_NOT_CONNECTED)
        return []

    payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "tools/list",
        "params": {},
    }
    try:
        with httpx.Client(timeout=10) as client:
            resp = client.post(get_nwiro_url(), json=payload)
            resp.raise_for_status()
            data = resp.json()
            return data.get("result", {}).get("tools", [])
    except Exception as exc:
        logger.warning("[Nwiro] tools/list failed: %s", exc)
        return []


def nwiro_call(tool_name: str, params: dict | None = None) -> str:
    """
    Appelle un outil Nwiro spécifique via MCP.

    Args:
        tool_name : nom de l'outil Nwiro (ex: "blueprint_create_actor")
        params : paramètres de l'outil (dict)

    Returns:
        Résultat de l'outil sous forme de string

    Raises:
        ConnectionError : si Nwiro n'est pas accessible
        ValueError : si l'outil n'existe pas ou les params sont invalides
    """
    if not nwiro_is_available():
        raise ConnectionError(UE5_NOT_CONNECTED)

    payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "tools/call",
        "params": {
            "name": tool_name,
            "arguments": params or {},
        },
    }

    try:
        with httpx.Client(timeout=30) as client:
            resp = client.post(get_nwiro_url(), json=payload)
            resp.raise_for_status()
            result = resp.json()

            if "error" in result:
                raise ValueError(
                    f"Erreur Nwiro : {result['error'].get('message', 'Erreur inconnue')}"
                )

            content = result.get("result", {}).get("content", [])
            if content and isinstance(content, list):
                return content[0].get("text", str(content))
            return str(result.get("result", "OK"))

    except httpx.TimeoutException:
        raise ConnectionError(f"Timeout Nwiro sur l'outil '{tool_name}' (30s)") from None
    except httpx.HTTPError as e:
        raise ConnectionError(f"Erreur HTTP Nwiro : {e}") from e


def nwiro_create_blueprint(class_name: str, parent_class: str = "Actor") -> str:
    """Raccourci : créer un Blueprint Actor."""
    return nwiro_call(
        "blueprint_create_actor",
        {"class_name": class_name, "parent_class": parent_class},
    )


def nwiro_compile_blueprint(blueprint_path: str) -> str:
    """Raccourci : compiler un Blueprint."""
    return nwiro_call("blueprint_compile", {"asset_path": blueprint_path})


def nwiro_spawn_actor(blueprint_path: str, location: dict | None = None) -> str:
    """Raccourci : spawner un Actor dans le niveau courant."""
    return nwiro_call(
        "world_spawn_actor",
        {
            "asset_path": blueprint_path,
            "location": location or {"x": 0, "y": 0, "z": 0},
        },
    )


# Raccourcis pour les outils les plus courants dans Wyrdheim/Naïa World
WYRDHEIM_TOOLS = {
    "create_npc_blueprint": lambda name: nwiro_call(
        "blueprint_create_actor",
        {"class_name": f"BP_{name}", "parent_class": "Character"},
    ),
    "create_faction_system": lambda: nwiro_call(
        "blueprint_create_actor",
        {"class_name": "BP_FactionManager", "parent_class": "GameInstance"},
    ),
    "create_interaction_component": lambda: nwiro_call(
        "blueprint_create_actor",
        {"class_name": "BP_InteractionComponent", "parent_class": "ActorComponent"},
    ),
}
