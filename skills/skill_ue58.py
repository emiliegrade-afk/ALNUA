"""Hub client for the UE5.8 studio server (DEC-017 / Vague A).

Replaces Nwiro as the Gaming bridge. Honest offline — never fabricates connection.
Server contract: SPEC_UE58_BRIDGE.md
"""
from __future__ import annotations

import logging
import os
from typing import Any
from urllib.parse import urljoin

import httpx

logger = logging.getLogger(__name__)

PROTOCOL_VERSION = "1"
DEFAULT_PORT = "8765"

UE58_NOT_CONFIGURED = (
    "Serveur UE5.8 non configuré — définir UE5_SERVER_URL ou UE58_HOST."
)
UE58_NOT_CONNECTED = (
    "Serveur UE5.8 injoignable — lancer le serveur studio (voir SPEC_UE58_BRIDGE.md)."
)

# Capability category tokens per Gaming agent (substring match, case-insensitive).
AGENT_CAP_FILTERS: dict[str, tuple[str, ...]] = {
    "ai_programmer": ("behavior", "bt", "blackboard", "ai"),
    "technical_artist": ("render", "shader", "nanite", "lod", "perf"),
    "vfx_artist": ("niagara", "vfx", "particle"),
}


def get_ue58_base_url() -> str | None:
    explicit = os.getenv("UE5_SERVER_URL", "").strip().rstrip("/")
    if explicit:
        return explicit
    host = os.getenv("UE58_HOST", "").strip()
    if not host:
        return None
    port = os.getenv("UE58_PORT", DEFAULT_PORT).strip() or DEFAULT_PORT
    return f"http://{host}:{port}"


def ue58_is_configured() -> bool:
    return get_ue58_base_url() is not None


def _auth_headers() -> dict[str, str]:
    key = os.getenv("UE58_API_KEY", "").strip()
    if not key:
        return {}
    return {"Authorization": f"Bearer {key}"}


def _get(path: str, *, timeout: float = 3.0) -> dict[str, Any]:
    base = get_ue58_base_url()
    if not base:
        raise ConnectionError(UE58_NOT_CONFIGURED)
    url = urljoin(base + "/", path.lstrip("/"))
    with httpx.Client(timeout=timeout) as client:
        resp = client.get(url, headers=_auth_headers())
        resp.raise_for_status()
        data = resp.json()
        return data if isinstance(data, dict) else {"raw": data}


def _post(path: str, body: dict[str, Any], *, timeout: float = 30.0) -> dict[str, Any]:
    base = get_ue58_base_url()
    if not base:
        raise ConnectionError(UE58_NOT_CONFIGURED)
    url = urljoin(base + "/", path.lstrip("/"))
    with httpx.Client(timeout=timeout) as client:
        resp = client.post(url, json=body, headers=_auth_headers())
        resp.raise_for_status()
        data = resp.json()
        return data if isinstance(data, dict) else {"raw": data}


def _put(path: str, body: dict[str, Any], *, timeout: float = 30.0) -> dict[str, Any]:
    base = get_ue58_base_url()
    if not base:
        raise ConnectionError(UE58_NOT_CONFIGURED)
    url = urljoin(base + "/", path.lstrip("/"))
    with httpx.Client(timeout=timeout) as client:
        resp = client.put(url, json=body, headers=_auth_headers())
        resp.raise_for_status()
        data = resp.json()
        return data if isinstance(data, dict) else {"raw": data}


def ue58_health() -> dict[str, Any]:
    """Health probe — never pretends the engine is up."""
    base = get_ue58_base_url()
    if not base:
        return {
            "ok": False,
            "configured": False,
            "connected": False,
            "bridge": "ue58",
            "protocol_version": PROTOCOL_VERSION,
            "error": UE58_NOT_CONFIGURED,
            "base_url": None,
        }
    try:
        data = _get("/health", timeout=2.0)
        return {
            "ok": True,
            "configured": True,
            "connected": True,
            "bridge": "ue58",
            "protocol_version": PROTOCOL_VERSION,
            "base_url": base,
            "server": data,
        }
    except Exception as exc:
        logger.debug("[UE58] health failed: %s", exc)
        return {
            "ok": False,
            "configured": True,
            "connected": False,
            "bridge": "ue58",
            "protocol_version": PROTOCOL_VERSION,
            "base_url": base,
            "error": UE58_NOT_CONNECTED,
            "detail": str(exc)[:200],
        }


def list_capabilities() -> list[dict[str, Any]]:
    if not ue58_is_configured():
        return []
    try:
        data = _get("/v1/capabilities", timeout=5.0)
        caps = data.get("capabilities") or []
        return [c for c in caps if isinstance(c, dict)]
    except Exception as exc:
        logger.warning("[UE58] capabilities failed: %s", exc)
        return []


def filter_capabilities_for_agent(
    agent_id: str, caps: list[dict[str, Any]] | None = None
) -> list[dict[str, Any]]:
    tokens = AGENT_CAP_FILTERS.get(agent_id, ())
    caps = caps if caps is not None else list_capabilities()
    if not tokens:
        return caps[:40]
    out: list[dict[str, Any]] = []
    for cap in caps:
        blob = " ".join(
            str(cap.get(k, "")) for k in ("id", "category", "description", "name")
        ).lower()
        if any(t in blob for t in tokens):
            out.append(
                {
                    "id": cap.get("id") or cap.get("name"),
                    "category": cap.get("category"),
                    "description": (cap.get("description") or "")[:200],
                }
            )
    return out[:40]


def probe_for_agent(agent_id: str) -> dict[str, Any]:
    """Agent-facing probe with role-filtered capabilities."""
    health = ue58_health()
    if not health.get("connected"):
        return {
            "ok": False,
            "connected": False,
            "configured": health.get("configured", False),
            "agent_id": agent_id,
            "bridge": "ue58",
            "error": health.get("error", UE58_NOT_CONNECTED),
            "capabilities": [],
            "legacy_nwiro": "Use /ue58-probe; nwiro-probe is legacy (DEC-017).",
        }
    caps = list_capabilities()
    filtered = filter_capabilities_for_agent(agent_id, caps)
    return {
        "ok": True,
        "connected": True,
        "configured": True,
        "agent_id": agent_id,
        "bridge": "ue58",
        "capabilities_total": len(caps),
        "capabilities": filtered,
        "server": health.get("server"),
    }


def chat(agent_id: str, message: str, session_id: str | None = None) -> dict[str, Any]:
    health = ue58_health()
    if not health.get("connected"):
        return {
            "ok": False,
            "connected": bool(health.get("connected")),
            "configured": health.get("configured", False),
            "error": health.get("error", UE58_NOT_CONNECTED),
        }
    body: dict[str, Any] = {"agent_id": agent_id, "message": message}
    if session_id:
        body["session_id"] = session_id
    try:
        data = _post("/v1/chat", body)
        return {
            "ok": True,
            "connected": True,
            "reply": data.get("reply", ""),
            "session_id": data.get("session_id"),
            "raw": data,
        }
    except Exception as exc:
        logger.warning("[UE58] chat failed: %s", exc)
        return {"ok": False, "connected": True, "error": str(exc)[:300]}


def gdd_sync(
    project_id: str,
    direction: str,
    payload: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Pull or push GDD JSON for a project. direction: pull | push."""
    direction = (direction or "").strip().lower()
    if direction not in ("pull", "push"):
        return {"ok": False, "error": "direction must be 'pull' or 'push'"}
    health = ue58_health()
    if not health.get("connected"):
        return {
            "ok": False,
            "configured": health.get("configured", False),
            "connected": False,
            "error": health.get("error", UE58_NOT_CONNECTED),
        }
    path = f"/v1/gdd/{project_id}"
    try:
        if direction == "pull":
            data = _get(path, timeout=15.0)
            return {"ok": True, "direction": "pull", "project_id": project_id, "gdd": data}
        data = _put(path, payload or {}, timeout=30.0)
        return {"ok": True, "direction": "push", "project_id": project_id, "result": data}
    except Exception as exc:
        logger.warning("[UE58] gdd_sync failed: %s", exc)
        return {"ok": False, "direction": direction, "error": str(exc)[:300]}


def call_tool(tool_id: str, arguments: dict[str, Any] | None = None) -> dict[str, Any]:
    """POST /v1/tools/call — editor-side action on the UE5.8 server."""
    tool_id = (tool_id or "").strip()
    if not tool_id:
        return {"ok": False, "error": "tool_id required"}
    health = ue58_health()
    if not health.get("connected"):
        return {
            "ok": False,
            "configured": health.get("configured", False),
            "connected": False,
            "error": health.get("error", UE58_NOT_CONNECTED),
        }
    try:
        data = _post(
            "/v1/tools/call",
            {"name": tool_id, "arguments": arguments or {}},
            timeout=120.0,
        )
        return {"ok": True, "connected": True, "tool_id": tool_id, "result": data}
    except Exception as exc:
        logger.warning("[UE58] tools/call failed: %s", exc)
        return {"ok": False, "connected": True, "tool_id": tool_id, "error": str(exc)[:300]}
