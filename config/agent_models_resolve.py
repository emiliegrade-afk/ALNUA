"""Persistent agent model config and resolution."""
from __future__ import annotations

import json
import logging
import os
from typing import Any

from config.agent_models_catalog import get_enriched_available_models
from config.agent_models_registry import (
    AGENT_TIERS,
    CODING_AGENT_IDS,
    TIER_DEFAULTS,
    agent_display,
    normalize_agent_id,
)
from config.agent_models_roles import AGENT_ROLE_MODELS
from config.paths import get_hub_repo_path

logger = logging.getLogger(__name__)

_CONFIG_FILE = get_hub_repo_path() / "data" / "agent_models.json"


def _load_config() -> dict[str, str]:
    """Lit data/agent_models.json — retourne {} si absent."""
    try:
        if _CONFIG_FILE.exists():
            return json.loads(_CONFIG_FILE.read_text(encoding="utf-8"))
    except Exception:
        pass
    return {}


def _save_config(config: dict[str, str]) -> None:
    _CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
    _CONFIG_FILE.write_text(json.dumps(config, indent=2, ensure_ascii=False), encoding="utf-8")


def get_model_for_agent(agent_id: str) -> str:
    """
    Retourne le modèle OpenRouter à utiliser pour un agent donné.

    Priorité :
      1. Var d'env AGENT_MODEL_{AGENT_ID_UPPER}
      2. Fichier data/agent_models.json (choix dans Paramètres)
      3. AGENT_ROLE_MODELS — modèle selon l'utilité métier (DEC-037)
      4. Tier auto selon AGENT_TIERS / TIER_DEFAULTS
    """
    agent_id = normalize_agent_id(agent_id)

    env_key = f"AGENT_MODEL_{agent_id.upper()}"
    env_val = os.getenv(env_key, "").strip()
    if env_val:
        return env_val

    file_config = _load_config()
    if agent_id in file_config and file_config[agent_id] != "auto":
        return file_config[agent_id]

    if agent_id in AGENT_ROLE_MODELS:
        return AGENT_ROLE_MODELS[agent_id]

    tier = AGENT_TIERS.get(agent_id, "standard")
    return TIER_DEFAULTS.get(tier, TIER_DEFAULTS["standard"])


def get_coding_model_for_agent(agent_id: str) -> str:
    """
    Modèle pour le pipeline de code (Hub Agent / Aider).

    Une seule source de vérité : même résolution que get_model_for_agent.
    """
    return get_model_for_agent(normalize_agent_id(agent_id))


def get_coding_model_openrouter(agent_id: str) -> str:
    """Slug OpenRouter API (sans préfixe openrouter/)."""
    from agents.base import to_api_model_slug

    return to_api_model_slug(get_coding_model_for_agent(agent_id))


def get_coding_model_aider(agent_id: str) -> str:
    """Slug attendu par Aider (--model openrouter/...)."""
    from agents.base import to_crewai_model_slug

    return to_crewai_model_slug(get_coding_model_for_agent(agent_id))


def get_all_agent_models() -> list[dict[str, Any]]:
    """Retourne la config complète pour tous les agents (pour le Hub)."""
    file_config = _load_config()
    enriched = get_enriched_available_models()
    agents = []
    for agent_id, tier in AGENT_TIERS.items():
        stored = file_config.get(agent_id, "auto")
        resolved = get_model_for_agent(agent_id)
        clean = resolved.replace("openrouter/", "")
        display = agent_display(agent_id)
        agents.append({
            "agent_id": agent_id,
            "tier": tier,
            "configured": stored,
            "resolved": resolved,
            "label": enriched.get(clean, {}).get("label", clean),
            "codes": agent_id in CODING_AGENT_IDS,
            "coding_model": resolved if agent_id in CODING_AGENT_IDS else None,
            "display_name": display["display_name"],
            "role_label": display["role_label"],
            "department": display["department"],
            "room": display.get("room", ""),
        })
    agents.sort(key=lambda a: (a["department"], a["display_name"]))
    return agents


def set_agent_model(agent_id: str, model: str) -> None:
    """Définit le modèle pour un agent. Utiliser "auto" pour revenir au mode automatique."""
    agent_id = normalize_agent_id(agent_id)
    config = _load_config()
    if model == "auto":
        config.pop(agent_id, None)
    else:
        config[agent_id] = model
    _save_config(config)
    logger.info("agent_models: %s → %s", agent_id, model)
