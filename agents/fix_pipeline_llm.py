"""LLM helper for fix_pipeline reviews."""
from __future__ import annotations

from agents.fix_pipeline_constants import REVIEW_MODEL


def _llm(system: str, user: str, model: str = REVIEW_MODEL) -> str:
    """OpenRouter via LLMClient — costs + retries."""
    from agents.base import LLMClient

    return LLMClient().complete(
        system,
        user,
        model=model,
        agent_id="qa",
        method_name="fix_pipeline_review",
        temperature=0.1,
        max_tokens=6000,
    )
