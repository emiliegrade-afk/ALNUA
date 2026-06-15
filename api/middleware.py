"""Hub API key middleware."""

from __future__ import annotations

import logging
import secrets

from fastapi import Request
from fastapi.responses import JSONResponse

from config.settings import get_settings

logger = logging.getLogger(__name__)
_warned_open_dev_api = False


def _is_beta_public(path: str, method: str) -> bool:
    """Tester-facing beta routes — no hub key (JWT on feedback routes in handlers)."""
    if method == "GET" and path.startswith("/beta/info/"):
        return True
    if path == "/beta/register" and method == "POST":
        return True
    if path == "/beta/feedback" and method == "POST":
        return True
    if path == "/beta/my-feedback" and method == "GET":
        return True
    return False


def _is_hub_api_key_exempt(path: str, method: str) -> bool:
    """Routes callable without X-Hub-Key (webhooks, public portals, affiliate redirects)."""
    if path == "/health":
        return True
    if _is_beta_public(path, method):
        return True
    if path == "/webhook/telegram" and method == "POST":
        return True
    if path == "/webhook/sentry" and method == "POST":
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


def _hub_key_enforcement_enabled() -> bool:
    """Prod/staging always enforce; dev skips when HUB_API_KEY is unset."""
    settings = get_settings()
    if settings.hub_api_key.strip():
        return True
    env = settings.environment.strip().lower()
    return env in {"production", "prod", "staging"}


def hub_api_key_valid(provided: str | None) -> bool:
    if not _hub_key_enforcement_enabled():
        return True
    expected = get_settings().hub_api_key
    if not provided or not expected:
        return False
    return secrets.compare_digest(provided, expected)


# Backward-compatible alias for split routers.
_hub_api_key_valid = hub_api_key_valid


async def hub_api_key_middleware(request: Request, call_next):
    """Require X-Hub-Key on all routes except health checks and public portals."""
    global _warned_open_dev_api
    path = request.url.path
    if _is_hub_api_key_exempt(path, request.method) or request.method == "OPTIONS":
        return await call_next(request)

    if not _hub_key_enforcement_enabled():
        if not _warned_open_dev_api:
            logger.warning(
                "HUB_API_KEY unset — dev open mode: protected routes skip X-Hub-Key checks"
            )
            _warned_open_dev_api = True
        return await call_next(request)

    expected = get_settings().hub_api_key
    provided = request.headers.get("X-Hub-Key")
    if not provided or not expected or not secrets.compare_digest(provided, expected):
        return JSONResponse(
            status_code=401,
            content={"detail": "Cle API invalide ou absente"},
        )
    return await call_next(request)


def register_middleware(app) -> None:
    app.middleware("http")(hub_api_key_middleware)
