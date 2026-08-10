"""Hub API middleware — auth, tenant context, rate limiting, metrics."""

from __future__ import annotations

import secrets

from fastapi import Request
from fastapi.responses import JSONResponse

from config.settings import get_settings
from models.tenant import TenantContext, resolve_tenant_id
from services.rate_limiter import ASSISTANT_LIMIT, API_LIMIT, assistant_limiter, api_limiter
from services.telemetry import RequestTimer, metrics


def _strip_v1_prefix(path: str) -> str:
    """Normalize /v1/foo → /foo for middleware route matching."""
    if path.startswith("/v1/"):
        return path[3:]  # keep leading slash: /v1/health → /health
    if path == "/v1":
        return "/"
    return path


def _is_beta_public(path: str, method: str) -> bool:
    """Tester-facing beta routes — no hub key (JWT on feedback routes in handlers)."""
    path = _strip_v1_prefix(path)
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
    path = _strip_v1_prefix(path)
    if path == "/health" or path == "/metrics":
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


def hub_api_key_valid(provided: str | None) -> bool:
    """HUB_API_KEY is required in every environment — settings validation
    already refuses to start the app without one (config/settings.py)."""
    expected = get_settings().hub_api_key
    if not provided or not expected:
        return False
    return secrets.compare_digest(provided, expected)


# Backward-compatible alias for split routers.
_hub_api_key_valid = hub_api_key_valid


async def hub_api_key_middleware(request: Request, call_next):
    """Require X-Hub-Key on all routes except health checks and public portals."""
    path = request.url.path
    if _is_hub_api_key_exempt(path, request.method) or request.method == "OPTIONS":
        return await call_next(request)

    expected = get_settings().hub_api_key
    provided = request.headers.get("X-Hub-Key")
    if not provided or not expected or not secrets.compare_digest(provided, expected):
        return JSONResponse(
            status_code=401,
            content={"detail": "Cle API invalide ou absente"},
        )
    return await call_next(request)


async def tenant_middleware(request: Request, call_next):
    """Resolve tenant from X-Tenant-ID and attach to request.state."""
    settings = get_settings()
    tenant_id = resolve_tenant_id(
        request.headers.get("X-Tenant-ID"),
        default=settings.default_tenant_id,
    )
    request.state.tenant = TenantContext(tenant_id=tenant_id)
    from database.tenant_scope import set_current_tenant_id

    set_current_tenant_id(tenant_id)
    return await call_next(request)


async def rate_limit_middleware(request: Request, call_next):
    """Rate-limit assistant chat and general API by client IP.

    Le limiteur général (`api_limiter`) protège contre un abus non
    authentifié — pas contre l'usage normal d'Emilie elle-même. Le Hub est
    un outil interne mono-utilisateur, pas une API publique multi-tenant :
    une requête porteuse d'un `X-Hub-Key` valide est déjà, par définition,
    du trafic légitime (une seule page comme `/rd` déclenche des dizaines
    d'appels authentifiés en parallèle — largement de quoi épuiser
    120/min sans qu'il y ait le moindre abus). Cette exemption tourne
    AVANT `hub_api_key_middleware` (ordre d'enregistrement dans
    `register_middleware` : ce middleware s'exécute avant celui-ci), donc
    la clé est revérifiée ici plutôt que de supposer qu'elle l'a déjà été.
    `assistant_limiter` reste inchangé : il limite le coût réel LLM/OpenRouter
    par message, pas la charge backend — un vrai frein à garder même pour
    du trafic authentifié."""
    settings = get_settings()
    if not settings.rate_limit_enabled:
        return await call_next(request)

    path = request.url.path
    norm_path = _strip_v1_prefix(path)
    client_ip = request.client.host if request.client else "unknown"

    if norm_path in ("/assistant/chat",):
        if not assistant_limiter.is_allowed(f"assistant:{client_ip}", ASSISTANT_LIMIT):
            return JSONResponse(
                status_code=429,
                content={"detail": "Trop de requêtes — réessaie dans 1 minute."},
            )
    elif (
        not _is_hub_api_key_exempt(path, request.method)
        and request.method != "OPTIONS"
        and not hub_api_key_valid(request.headers.get("X-Hub-Key"))
    ):
        if not api_limiter.is_allowed(f"api:{client_ip}", API_LIMIT):
            return JSONResponse(
                status_code=429,
                content={"detail": "Rate limit API atteint."},
            )

    return await call_next(request)


async def metrics_middleware(request: Request, call_next):
    """Record request latency for Prometheus."""
    path = request.url.path
    with RequestTimer("http_request_duration_ms", {"path": path.split("?")[0][:80]}):
        response = await call_next(request)
    metrics.inc("http_requests_total", labels={"status": str(response.status_code)})
    return response


def register_middleware(app) -> None:
    app.middleware("http")(metrics_middleware)
    app.middleware("http")(tenant_middleware)
    app.middleware("http")(rate_limit_middleware)
    # Register before hub_api_key so hub key runs first (last registered = outermost).
    from api.middleware_mcp import mcp_permission_middleware

    app.middleware("http")(mcp_permission_middleware)
    app.middleware("http")(hub_api_key_middleware)
