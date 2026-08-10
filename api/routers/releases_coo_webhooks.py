"""COO briefing/instruction and Telegram webhook routes."""

from __future__ import annotations

from api.route_common import *  # noqa: F403

router = APIRouter()


@router.post("/agents/coo/briefing")
def coo_briefing() -> dict[str, str]:
    agent = COOAgent()
    briefing = agent.run_daily_briefing()
    return {"briefing": briefing}


@router.post("/agents/coo/instruction", response_model=COOInstructionResponse)
def coo_instruction(body: COOInstruction) -> COOInstructionResponse:
    try:
        result = get_coo_agent().process_message(body.instruction, body.project)
        return COOInstructionResponse(**result)
    except Exception as exc:
        logger.exception("COO instruction failed: %s", exc)
        return COOInstructionResponse(
            response=f"Erreur COO : {exc}",
            issue_created=False,
        )


@router.post("/webhook/telegram")
async def telegram_webhook(request: Request) -> dict[str, bool]:
    """Receives Telegram updates (webhook mode — production)."""
    import secrets

    settings = get_settings()
    if not settings.telegram_bot_token:
        raise HTTPException(status_code=503, detail="Telegram bot not configured")

    webhook_secret = settings.telegram_webhook_secret.strip()
    env = settings.environment.strip().lower()
    is_prod = env in {"production", "prod", "staging"}
    if webhook_secret:
        provided = request.headers.get("X-Telegram-Bot-Api-Secret-Token", "")
        if not provided or not secrets.compare_digest(provided, webhook_secret):
            raise HTTPException(status_code=401, detail="Telegram webhook secret invalide")
    elif is_prod:
        raise HTTPException(
            status_code=503,
            detail="TELEGRAM_WEBHOOK_SECRET requis en production",
        )

    update_data = await request.json()
    await get_telegram_bot().process_update(update_data)
    return {"ok": True}


@router.post("/webhook/telegram/secretary")
async def telegram_secretary_webhook(request: Request) -> dict[str, bool]:
    """Webhook Telegram — bot Nadia (secrétaire)."""
    import secrets

    settings = get_settings()
    if not settings.telegram_secretary_bot_token:
        raise HTTPException(status_code=503, detail="Telegram secretary bot not configured")

    webhook_secret = settings.telegram_secretary_webhook_secret.strip()
    env = settings.environment.strip().lower()
    is_prod = env in {"production", "prod", "staging"}
    if webhook_secret:
        provided = request.headers.get("X-Telegram-Bot-Api-Secret-Token", "")
        if not provided or not secrets.compare_digest(provided, webhook_secret):
            raise HTTPException(status_code=401, detail="Telegram secretary webhook secret invalide")
    elif is_prod:
        raise HTTPException(
            status_code=503,
            detail="TELEGRAM_SECRETARY_WEBHOOK_SECRET requis en production",
        )

    from bots.telegram_secretary_bot import get_telegram_secretary_bot

    update_data = await request.json()
    await get_telegram_secretary_bot().process_update(update_data)
    return {"ok": True}
