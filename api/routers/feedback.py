"""Agent response feedback — thumbs up/down + optional regen trigger."""

from __future__ import annotations

from api.route_common import *  # noqa: F403

import logging
import uuid
from typing import Any, Literal

from database.tenant_scope import get_current_tenant_id
from services.analytics import record_feedback

logger = logging.getLogger(__name__)

router = APIRouter()


class AgentFeedbackRequest(BaseModel):
    agent_id: str = Field(min_length=1, max_length=64)
    response_id: str = Field(min_length=1, max_length=128)
    rating: Literal[1, -1]
    comment: str | None = Field(default=None, max_length=2000)
    original_message: str | None = Field(default=None, max_length=4000)
    original_response: str | None = Field(default=None, max_length=8000)


class AgentFeedbackResponse(BaseModel):
    id: str
    recorded: bool
    regen_triggered: bool = False
    regen_response: str | None = None
    job_id: str | None = None


def _run_regen(agent_id: str, prompt: str) -> str:
    if agent_id == "secretary":
        from agents.secretary_agent import SecretaryAgent
        return SecretaryAgent().handle_instruction(prompt)
    from agents.coo_agent import COOAgent
    return COOAgent().handle_instruction(prompt)


@router.post("/feedback/agent", response_model=AgentFeedbackResponse)
def submit_agent_feedback(body: AgentFeedbackRequest) -> AgentFeedbackResponse:
    """Record 👍/👎 on an agent response. Negative triggers regen when context provided."""
    from services.input_sanitizer import sanitize_user_input

    feedback_id = uuid.uuid4().hex[:16]
    comment = sanitize_user_input(body.comment or "", max_length=2000)
    record_feedback(body.agent_id, rating=body.rating, response_id=body.response_id)

    from services.feedback_store import save_agent_feedback

    row = save_agent_feedback(
        agent_id=body.agent_id,
        response_id=body.response_id,
        rating=body.rating,
        comment=comment,
        original_message=body.original_message,
        original_response=body.original_response,
    )
    if row and row.get("id"):
        feedback_id = str(row["id"])

    regen_response: str | None = None
    regen_triggered = False
    job_id: str | None = None

    if body.rating == -1 and body.original_message and body.original_response:
        regen_triggered = True
        tenant_id = get_current_tenant_id()
        correction = comment or "La réponse précédente n'était pas satisfaisante."
        prompt = (
            f"L'utilisateur a rejeté cette réponse :\n{body.original_response[:1500]}\n\n"
            f"Feedback : {correction}\n\n"
            f"Message original : {body.original_message[:1500]}\n\n"
            "Régénère une meilleure réponse."
        )
        try:
            from agents.personalities import apply_personality, get_personality
            from config.agent_operating_spec import get_system_prompt

            overrides = get_personality(tenant_id)
            if overrides:
                _ = apply_personality(get_system_prompt(body.agent_id), overrides)

            from services.rq_queue import enqueue_task

            job_id = enqueue_task(_run_regen, body.agent_id, prompt)
            if job_id is None:
                regen_response = _run_regen(body.agent_id, prompt)
        except Exception as exc:
            logger.warning("Feedback regen failed: %s", exc)
            regen_response = f"Regénération impossible : {exc}"

    if body.rating == -1:
        try:
            from skills.skill_mem0 import remember

            lesson = f"[FEEDBACK-] {comment or 'Réponse rejetée'} — response_id={body.response_id}"
            remember(body.agent_id, lesson)
        except Exception:
            pass

    return AgentFeedbackResponse(
        id=feedback_id,
        recorded=True,
        regen_triggered=regen_triggered,
        regen_response=regen_response,
        job_id=job_id,
    )


@router.get("/feedback/agent/stats")
def feedback_stats(agent_id: str | None = None) -> dict[str, Any]:
    """Aggregate feedback from Supabase agent_feedback (tenant-scoped)."""
    try:
        from database.supabase_client import get_supabase

        db = get_supabase()
        filters: dict[str, Any] = {}
        if agent_id:
            filters["agent_id"] = agent_id
        rows = db.select("agent_feedback", filters=filters or None, limit=500)
    except Exception:
        rows = []

    positive = sum(1 for r in rows if r.get("rating") == 1)
    negative = sum(1 for r in rows if r.get("rating") == -1)
    total = len(rows)
    return {
        "total": total,
        "positive": positive,
        "negative": negative,
        "satisfaction_pct": round(100 * positive / total, 1) if total else 0,
        "tenant_id": get_current_tenant_id(),
    }
