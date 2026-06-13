"""Hub API key middleware."""

from __future__ import annotations

from fastapi import Request
from fastapi.responses import JSONResponse

from config.settings import get_settings


def _is_hub_api_key_exempt(path: str, method: str) -> bool:
    """Routes callable without X-Hub-Key (webhooks, public portals, affiliate redirects)."""
    if path == "/health":
        return True
    if path.startswith("/beta/"):
        return True
    if path == "/webhook/telegram" and method == "POST":
        return True
    if path.startswith("/go/"):
        return True
    if path.startswith("/rnd/product/"):
        return True
    if path.startswith("/waitlist/info/") or path.startswith("/waitlist/count/"):
        return True
    if path == "/waitlist/join" and method == "POST":
        return True
    if path == "/partnerships/request" and method == "POST":
        return True
    if method == "GET" and path.startswith("/rnd/dossiers/") and path.endswith("/assets/file"):
        return True
    return False


def hub_api_key_valid(provided: str | None) -> bool:
    expected = get_settings().hub_api_key
    return bool(provided and expected and provided == expected)


# Backward-compatible alias for split routers.
_hub_api_key_valid = hub_api_key_valid


async def hub_api_key_middleware(request: Request, call_next):
    """Require X-Hub-Key on all routes except health checks and beta portal."""
    path = request.url.path
    if _is_hub_api_key_exempt(path, request.method) or request.method == "OPTIONS":
        return await call_next(request)

    expected = get_settings().hub_api_key
    provided = request.headers.get("X-Hub-Key")
    if not provided or provided != expected:
        return JSONResponse(
            status_code=401,
            content={"detail": "Cle API invalide ou absente"},
        )
    return await call_next(request)


def register_middleware(app) -> None:
    app.middleware("http")(hub_api_key_middleware)
