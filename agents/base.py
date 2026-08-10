"""Shared utilities for ALNUA Hub agents — public facade."""

from __future__ import annotations

from agents.base_json import parse_json_response
from agents.base_learning import run_with_learning, run_with_learning_async
from agents.base_llm import LLMClient
from agents.base_logging import log_agent_action
from agents.base_models import (
    build_crewai_llm,
    normalize_openrouter_model,
    openrouter_chat_completions_url,
    resolve_openrouter_model,
    to_api_model_slug,
    to_crewai_model_slug,
)

__all__ = [
    "LLMClient",
    "build_crewai_llm",
    "log_agent_action",
    "normalize_openrouter_model",
    "openrouter_chat_completions_url",
    "parse_json_response",
    "resolve_openrouter_model",
    "run_with_learning",
    "run_with_learning_async",
    "to_api_model_slug",
    "to_crewai_model_slug",
]
