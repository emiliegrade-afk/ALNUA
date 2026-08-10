"""HTTP middleware — MCP Capability Guard (DEC-026 progressive)."""

from __future__ import annotations

from fastapi import Request
from fastapi.responses import JSONResponse


async def mcp_permission_middleware(request: Request, call_next):
    """Deny mapped mutating routes when MCP client lacks capability."""
    if request.method == "OPTIONS":
        return await call_next(request)
    try:
        from services.mcp_permission_guard import enforce_mcp_http

        denied = enforce_mcp_http(
            request.method,
            request.url.path,
            request.headers,
        )
    except Exception:
        denied = None
    if denied is not None:
        return JSONResponse(
            status_code=403,
            content={
                "detail": (
                    f"MCP capability denied: agent={denied.get('agent_id')!r} "
                    f"capability={denied.get('capability')!r} "
                    f"reason={denied.get('reason')}"
                ),
                "permission": denied,
            },
        )
    return await call_next(request)
