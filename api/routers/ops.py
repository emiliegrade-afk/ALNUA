"""Production ops — Sentry webhook + status (Phase 4)."""

from __future__ import annotations

from api.route_common import *  # noqa: F403

router = APIRouter(tags=["ops"])


@router.post("/webhook/sentry")
async def sentry_webhook(request: Request) -> dict[str, Any]:
    """
    Sentry Issue Alert webhook.
    Configure in Sentry → Settings → Integrations → Webhooks.
    Header: Sentry-Hook-Signature (HMAC-SHA256).
    """
    from config.settings import get_settings
    from services.production_ops import run_sentry_webhook

    body = await request.body()
    signature = request.headers.get("Sentry-Hook-Signature")
    settings = get_settings()

    import json

    try:
        payload = json.loads(body.decode("utf-8") or "{}")
    except json.JSONDecodeError as exc:
        raise HTTPException(status_code=400, detail="invalid JSON") from exc

    secret = settings.sentry_webhook_secret
    create_issue = settings.sentry_auto_issue

    result = run_sentry_webhook(
        payload,
        body=body,
        signature=signature,
        secret=secret,
        create_issue=create_issue,
        allow_unsigned=settings.sentry_webhook_allow_unsigned,
    )
    if not result.get("success"):
        raise HTTPException(status_code=401, detail=result.get("error", "unauthorized"))
    return result


@router.get("/ops/production/status")
def production_ops_status() -> dict[str, Any]:
    """Cockpit Phase 4 — Sentry + error journal + pipeline."""
    from services.production_ops import get_production_ops_status

    return get_production_ops_status()


@router.post("/ops/production/simulate")
def production_ops_simulate(body: SentrySimulateRequest) -> dict[str, Any]:
    """Inject a test Sentry event (dev — requires X-Hub-Key)."""
    from services.production_ops import simulate_sentry_event

    return simulate_sentry_event(
        title=body.title,
        message=body.message,
        project_slug=body.project_slug,
        level=body.level,
        dry_run=body.dry_run,
    )
