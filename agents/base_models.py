"""OpenRouter / CrewAI model slug helpers."""

from __future__ import annotations

from config.llm_runtime import http_timeout_s
from config.settings import get_settings

# Deprecated on OpenRouter — auto-upgrade at call time
_MODEL_ALIASES: dict[str, str] = {
    "x-ai/grok-3": "x-ai/grok-4.3",
}


def to_api_model_slug(model: str) -> str:
    """OpenRouter REST API expects provider/model without openrouter/ prefix."""
    m = model.strip()
    if m.startswith("openrouter/"):
        return m[len("openrouter/") :]
    return m


def normalize_openrouter_model(model: str) -> str:
    """Resolve API slug + replace known-dead model IDs."""
    slug = to_api_model_slug(model)
    return _MODEL_ALIASES.get(slug, slug)


def openrouter_chat_completions_url(base_url: str) -> str:
    """Always return .../api/v1/chat/completions (never double-path)."""
    base = (base_url or "https://openrouter.ai/api/v1").strip().rstrip("/")
    if base.endswith("/chat/completions"):
        return base
    return f"{base}/chat/completions"


def to_crewai_model_slug(model: str) -> str:
    """CrewAI LLM wrapper expects openrouter/provider/model."""
    m = model.strip()
    if not m.startswith("openrouter/"):
        return f"openrouter/{m}"
    return m


def resolve_openrouter_model(agent_id: str) -> str:
    """Resolved model slug for OpenRouter REST API calls."""
    from config.agent_models import get_model_for_agent

    return normalize_openrouter_model(get_model_for_agent(agent_id))


def build_crewai_llm(agent_id: str, temperature: float = 0.3):
    """CrewAI LLM instance using per-agent model config + prompt-cache params."""
    from crewai import LLM

    from services.openrouter_prompt_cache import crewai_additional_params

    settings = get_settings()
    model = to_crewai_model_slug(resolve_openrouter_model(agent_id))
    extra = crewai_additional_params(agent_id, settings=settings)
    return LLM(
        model=model,
        base_url=settings.openrouter_base_url,
        api_key=settings.openrouter_api_key,
        temperature=temperature,
        timeout=http_timeout_s(settings),
        additional_params=extra or None,
    )
