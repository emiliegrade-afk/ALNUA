"""ALNUA Hub agents package — lazy exports to support `python -m agents.coo_agent`."""

from __future__ import annotations

import importlib
from typing import Any

from agents.base import (
    LLMClient,
    build_crewai_llm,
    log_agent_action,
    parse_json_response,
    resolve_openrouter_model,
)

__all__ = [
    "LLMClient",
    "build_crewai_llm",
    "resolve_openrouter_model",
    "log_agent_action",
    "parse_json_response",
    "COOAgent",
    "route_to_agent",
    "PMAgent",
    "QAAgent",
    "ContentAgent",
    "BrainstormAgent",
    "SpecAgent",
    "GameDirectorAgent",
    "DevGamingAgent",
    "HardwareAgent",
    "EmbeddedDevAgent",
    "MarketingAgent",
    "DevAppAgent",
    "SecretaryAgent",
    "DevBackendAgent",
    "AccountantAgent",
    "DevFrontendAgent",
    "DevIntegratorAgent",
    "ContentAppAgent",
    "ContentGamingAgent",
    "ContentRoboAgent",
    "ContentCompanyAgent",
]

_LAZY_EXPORTS: dict[str, tuple[str, str]] = {
    "COOAgent": ("agents.coo_agent", "COOAgent"),
    "route_to_agent": ("agents.coo_agent", "route_to_agent"),
    "PMAgent": ("agents.pm_agent", "PMAgent"),
    "QAAgent": ("agents.qa_agent", "QAAgent"),
    "ContentAgent": ("agents.content_agent", "ContentAgent"),
    "BrainstormAgent": ("agents.brainstorm_agent", "BrainstormAgent"),
    "SpecAgent": ("agents.spec_agent", "SpecAgent"),
    "GameDirectorAgent": ("agents.game_director_agent", "GameDirectorAgent"),
    "DevGamingAgent": ("agents.dev_gaming_agent", "DevGamingAgent"),
    "HardwareAgent": ("agents.hardware_agent", "HardwareAgent"),
    "EmbeddedDevAgent": ("agents.embedded_dev_agent", "EmbeddedDevAgent"),
    "MarketingAgent": ("agents.marketing_agent", "MarketingAgent"),
    "DevAppAgent": ("agents.dev_app_agent", "DevAppAgent"),
    "SecretaryAgent": ("agents.secretary_agent", "SecretaryAgent"),
    "DevBackendAgent": ("agents.dev_backend_agent", "DevBackendAgent"),
    "AccountantAgent": ("agents.accountant_agent", "AccountantAgent"),
    "DevFrontendAgent": ("agents.dev_frontend_agent", "DevFrontendAgent"),
    "DevIntegratorAgent": ("agents.dev_integrator_agent", "DevIntegratorAgent"),
    "ContentAppAgent": ("agents.content_app_agent", "ContentAppAgent"),
    "ContentGamingAgent": ("agents.content_gaming_agent", "ContentGamingAgent"),
    "ContentRoboAgent": ("agents.content_robo_agent", "ContentRoboAgent"),
    "ContentCompanyAgent": ("agents.content_company_agent", "ContentCompanyAgent"),
}


def __getattr__(name: str) -> Any:
    if name in _LAZY_EXPORTS:
        module_path, attr = _LAZY_EXPORTS[name]
        return getattr(importlib.import_module(module_path), attr)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
