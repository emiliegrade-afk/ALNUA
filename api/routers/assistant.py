"""Unified NL assistant — Aria (COO) + Nadia (secretary)."""

from __future__ import annotations

from api.route_common import *  # noqa: F403

router = APIRouter()


@router.get("/assistant/connections")
def assistant_connections() -> dict[str, Any]:
    """Composio OAuth status for CEO mailbox + calendar."""
    from services.secretary_composio import (
        composio_user_id,
        connection_status_text,
        list_ceo_connections,
    )

    return {
        "composio_user_id": composio_user_id(),
        "apps": list_ceo_connections(),
        "summary": connection_status_text(),
    }


@router.post("/assistant/connect/{app_name}")
def assistant_connect_app(app_name: str) -> dict[str, str]:
    """OAuth link for Gmail or Google Calendar."""
    from services.secretary_composio import get_oauth_link_for_ceo

    link = get_oauth_link_for_ceo(app_name)
    return {"app": app_name.upper(), "oauth_url": link}


@router.post("/assistant/chat", response_model=AssistantChatResponse)
async def assistant_chat_endpoint(body: AssistantChatRequest) -> AssistantChatResponse:
    """Natural-language chat with Aria or Nadia (auto-routing by default)."""
    from services.assistant_router import assistant_chat_async
    from services.input_sanitizer import sanitize_user_input
    from services.rate_limiter import ASSISTANT_LIMIT, assistant_limiter
    from services.telemetry import RequestTimer, metrics

    safe_message = sanitize_user_input(body.message, max_length=4000)
    if not safe_message:
        raise HTTPException(status_code=400, detail="Message vide après sanitization")

    session_key = body.session_id or "hub"
    if not assistant_limiter.is_allowed(f"session:{session_key}", ASSISTANT_LIMIT):
        raise HTTPException(status_code=429, detail="Trop de messages — pause 1 minute.")

    try:
        with RequestTimer("assistant_chat_ms", {"agent": body.agent}):
            result = await assistant_chat_async(
                safe_message,
                agent=body.agent,
                project=body.project,
                session_id=body.session_id,
                channel="hub",
            )
        response_id = uuid.uuid4().hex[:16]
        result["response_id"] = response_id
        metrics.inc("assistant_chat_total", labels={"agent": result.get("agent_id", "unknown")})
        return AssistantChatResponse(**result)
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("assistant/chat failed")
        return AssistantChatResponse(
            agent_id="coo",
            agent_name="Aria Voss",
            response=f"Désolée — erreur assistant : {exc}",
            issue_created=False,
        )


@router.post("/agents/secretary/instruction", response_model=AssistantChatResponse)
def secretary_instruction(body: AssistantChatRequest) -> AssistantChatResponse:
    """Direct NL entry for Nadia (same shape as assistant chat)."""
    from agents.secretary_agent import SecretaryAgent

    try:
        sid = body.session_id or "hub"
        response = SecretaryAgent().handle_instruction(body.message, session_id=sid)
        return AssistantChatResponse(
            agent_id="secretary",
            agent_name="Nadia Faure",
            response=response,
            issue_created=False,
        )
    except Exception as exc:
        logger.exception("secretary instruction failed")
        return AssistantChatResponse(
            agent_id="secretary",
            agent_name="Nadia Faure",
            response=f"Erreur : {exc}",
            issue_created=False,
        )
