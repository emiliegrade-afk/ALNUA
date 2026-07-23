"""Shared runtime state for WebSocket handlers and the COO singleton."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from fastapi import WebSocket

from agents.coo_agent import COOAgent
from api.middleware import hub_api_key_valid

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)


class ConnectionManager:
    def __init__(self) -> None:
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket) -> None:
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket) -> None:
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def broadcast(self, message: dict) -> None:
        for connection in list(self.active_connections):
            try:
                await connection.send_json(message)
            except Exception:
                self.disconnect(connection)


ws_manager = ConnectionManager()
_coo_agent_singleton: COOAgent | None = None


def get_coo_agent() -> COOAgent:
    global _coo_agent_singleton
    if _coo_agent_singleton is None:
        _coo_agent_singleton = COOAgent()
    return _coo_agent_singleton


# Backward-compatible alias used by split routers.
_get_coo_agent = get_coo_agent


async def accept_authenticated_websocket(websocket: WebSocket) -> bool:
    key = websocket.headers.get("x-hub-key") or websocket.query_params.get("hub_key")
    if not hub_api_key_valid(key):
        await websocket.close(code=1008, reason="Cle API invalide ou absente")
        return False
    await ws_manager.connect(websocket)
    return True


_accept_authenticated_websocket = accept_authenticated_websocket

__all__ = [
    "ConnectionManager",
    "accept_authenticated_websocket",
    "get_coo_agent",
    "hub_api_key_valid",
    "ws_manager",
    "_accept_authenticated_websocket",
    "_get_coo_agent",
]
