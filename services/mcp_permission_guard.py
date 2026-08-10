"""MCP PermissionGuard — progressive route interception (DEC-026).

When a client sends X-MCP-Agent (Cursor / MCP), mapped mutating routes must
pass Capability Pack checks before the handler runs. Call-site guards remain
the primary choke for non-MCP traffic.
"""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)

MCP_AGENT_HEADER = "X-MCP-Agent"
MCP_CLIENT_HEADER = "X-MCP-Client"
AGENT_ID_HEADER = "X-Agent-Id"


def mcp_guard_enabled() -> bool:
    try:
        from config.settings import get_settings

        settings = get_settings()
        if not bool(getattr(settings, "permission_guard_enabled", True)):
            return False
        return bool(getattr(settings, "permission_guard_mcp_enabled", True))
    except Exception:
        return True


def extract_mcp_agent(headers: Any) -> str | None:
    """Resolve acting agent from MCP-identifying headers."""
    get = headers.get if hasattr(headers, "get") else lambda _k, default=None: default
    mcp_flag = str(get(MCP_CLIENT_HEADER) or get(MCP_CLIENT_HEADER.lower()) or "").strip()
    agent = (
        str(get(MCP_AGENT_HEADER) or get(MCP_AGENT_HEADER.lower()) or "").strip()
        or str(get(AGENT_ID_HEADER) or get(AGENT_ID_HEADER.lower()) or "").strip()
    )
    if agent:
        return agent
    if mcp_flag in {"1", "true", "yes"}:
        return "cursor"
    return None


def is_mcp_identified_request(headers: Any) -> bool:
    get = headers.get if hasattr(headers, "get") else lambda _k, default=None: default
    if get(MCP_AGENT_HEADER) or get(MCP_AGENT_HEADER.lower()):
        return True
    flag = str(get(MCP_CLIENT_HEADER) or get(MCP_CLIENT_HEADER.lower()) or "").strip().lower()
    return flag in {"1", "true", "yes"}


def enforce_mcp_http(
    method: str,
    path: str,
    headers: Any,
) -> dict[str, Any] | None:
    """
    Return None if allowed / not applicable.
    Return decision dict if denied (caller returns HTTP 403).
    """
    if not mcp_guard_enabled():
        return None
    if (path or "").startswith("/mcp"):
        # Protocol surface itself — tools invoke real API paths.
        return None
    if not is_mcp_identified_request(headers):
        return None

    from config.mcp_capability_routes import match_mcp_capability
    from services.permission_guard import check_capability

    capability = match_mcp_capability(method, path)
    if not capability:
        return None

    agent_id = extract_mcp_agent(headers) or "cursor"
    decision = check_capability(
        agent_id,
        capability,
        resource=f"mcp:{method}:{(path or '')[:120]}",
        meta={"source": "mcp_permission_guard"},
    )
    if decision.get("allowed"):
        return None
    logger.warning(
        "mcp_permission_guard DENY agent=%s cap=%s path=%s",
        agent_id,
        capability,
        path,
    )
    return decision


__all__ = [
    "AGENT_ID_HEADER",
    "MCP_AGENT_HEADER",
    "MCP_CLIENT_HEADER",
    "enforce_mcp_http",
    "extract_mcp_agent",
    "is_mcp_identified_request",
    "mcp_guard_enabled",
]
