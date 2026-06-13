"""
config/agent_models.py — Sélection de modèle LLM par agent.

Priorité de résolution (du plus spécifique au plus général) :
  1. Variable d'env  AGENT_MODEL_{AGENT_ID}   (ex: AGENT_MODEL_COO=openrouter/anthropic/claude-opus-4)
  2. Fichier de config  data/agent_models.json  (choix dans Paramètres /settings)
  3. Tier automatique basé sur le rôle de l'agent (premium / standard / fast)

Mode AUTO : modèle selon le tier de l'agent. Les choix dans Paramètres priment sur tout.
"""
from __future__ import annotations

import json
import logging
import os
from functools import lru_cache
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Catalogue de modèles disponibles
# ---------------------------------------------------------------------------

AVAILABLE_MODELS: dict[str, dict[str, str]] = {
    # ── Premium occidental — Claude Sonnet / Opus / Fable ─────────────────
    "anthropic/claude-sonnet-4":        {"label": "Claude Sonnet 4",        "tier": "premium", "region": "west"},
    "anthropic/claude-sonnet-4.5":      {"label": "Claude Sonnet 4.5",      "tier": "premium", "region": "west"},
    "anthropic/claude-sonnet-4.6":      {"label": "Claude Sonnet 4.6",      "tier": "premium", "region": "west"},
    "anthropic/claude-opus-4":          {"label": "Claude Opus 4",          "tier": "premium", "region": "west"},
    "anthropic/claude-opus-4.1":        {"label": "Claude Opus 4.1",        "tier": "premium", "region": "west"},
    "anthropic/claude-opus-4.5":        {"label": "Claude Opus 4.5",        "tier": "premium", "region": "west"},
    "anthropic/claude-opus-4.6":        {"label": "Claude Opus 4.6",        "tier": "premium", "region": "west"},
    "anthropic/claude-opus-4.7":        {"label": "Claude Opus 4.7",        "tier": "premium", "region": "west"},
    "anthropic/claude-opus-4.8":        {"label": "Claude Opus 4.8",        "tier": "premium", "region": "west"},
    "anthropic/claude-fable-5":         {"label": "Claude Fable 5",         "tier": "premium", "region": "west"},
    # ── Premium occidental — GPT ───────────────────────────────────────────
    "openai/gpt-4o":                    {"label": "GPT-4o",                 "tier": "premium", "region": "west"},
    "openai/gpt-4-turbo":               {"label": "GPT-4 Turbo",            "tier": "premium", "region": "west"},
    "openai/gpt-5":                     {"label": "GPT-5",                  "tier": "premium", "region": "west"},
    "openai/gpt-5.1":                   {"label": "GPT-5.1",                "tier": "premium", "region": "west"},
    "openai/gpt-5.2":                   {"label": "GPT-5.2",                "tier": "premium", "region": "west"},
    "openai/gpt-5.4":                   {"label": "GPT-5.4",                "tier": "premium", "region": "west"},
    "openai/gpt-5.5":                   {"label": "GPT-5.5",                "tier": "premium", "region": "west"},
    "openai/gpt-5-pro":                 {"label": "GPT-5 Pro",              "tier": "premium", "region": "west"},
    "openai/gpt-5.4-pro":               {"label": "GPT-5.4 Pro",            "tier": "premium", "region": "west"},
    "openai/gpt-5.5-pro":               {"label": "GPT-5.5 Pro",            "tier": "premium", "region": "west"},
    # ── Premium occidental — autres ──────────────────────────────────────
    "google/gemini-2.5-pro":            {"label": "Gemini 2.5 Pro",         "tier": "premium", "region": "west"},
    "x-ai/grok-3":                      {"label": "Grok 3",                 "tier": "premium", "region": "west"},
    # ── Premium Chine — raisonnement profond, agents ───────────────────────
    "deepseek/deepseek-r1-0528":        {"label": "DeepSeek R1 0528",       "tier": "premium", "region": "cn"},
    "moonshotai/kimi-k2.6":             {"label": "Kimi K2.6",              "tier": "premium", "region": "cn"},
    "z-ai/glm-4.6":                     {"label": "GLM 4.6",                "tier": "premium", "region": "cn"},
    # ── Standard occidental — Claude rapide / GPT mid ─────────────────────
    "anthropic/claude-opus-4.6-fast":   {"label": "Claude Opus 4.6 Fast",   "tier": "standard", "region": "west"},
    "anthropic/claude-opus-4.7-fast":   {"label": "Claude Opus 4.7 Fast",   "tier": "standard", "region": "west"},
    "anthropic/claude-opus-4.8-fast":   {"label": "Claude Opus 4.8 Fast",   "tier": "standard", "region": "west"},
    "anthropic/claude-haiku-4-5":       {"label": "Claude Haiku 4.5",       "tier": "standard", "region": "west"},
    "openai/gpt-4.1":                   {"label": "GPT-4.1",                "tier": "standard", "region": "west"},
    "openai/gpt-4o-mini":               {"label": "GPT-4o Mini",            "tier": "standard", "region": "west"},
    "openai/gpt-5-mini":                {"label": "GPT-5 Mini",             "tier": "standard", "region": "west"},
    "openai/gpt-5.1-codex":             {"label": "GPT-5.1 Codex",          "tier": "standard", "region": "west"},
    "openai/gpt-5.2-codex":             {"label": "GPT-5.2 Codex",          "tier": "standard", "region": "west"},
    "openai/gpt-5.3-codex":             {"label": "GPT-5.3 Codex",          "tier": "standard", "region": "west"},
    "openai/gpt-5.4-mini":              {"label": "GPT-5.4 Mini",           "tier": "standard", "region": "west"},
    "google/gemini-2.0-flash-001":      {"label": "Gemini 2.0 Flash",       "tier": "standard", "region": "west"},
    "minimax/minimax-m1":               {"label": "MiniMax M1",             "tier": "standard", "region": "cn"},
    # ── Standard Chine — code & agents ───────────────────────────────────
    "minimax/minimax-m2.7":             {"label": "MiniMax M2.7",           "tier": "standard", "region": "cn"},
    "minimax/minimax-m2.7-highspeed":   {"label": "MiniMax M2.7 Rapide",    "tier": "standard", "region": "cn"},
    "deepseek/deepseek-chat-v3.1":      {"label": "DeepSeek V3.1",          "tier": "standard", "region": "cn"},
    "deepseek/deepseek-chat-v3-0324":   {"label": "DeepSeek V3",            "tier": "standard", "region": "cn"},
    "deepseek/deepseek-v3.2":           {"label": "DeepSeek V3.2",          "tier": "standard", "region": "cn"},
    "qwen/qwen3-coder":                 {"label": "Qwen3 Coder 480B",       "tier": "standard", "region": "cn"},
    "qwen/qwen3-235b-a22b":             {"label": "Qwen3 235B",             "tier": "standard", "region": "cn"},
    "z-ai/glm-4.5":                     {"label": "GLM 4.5",                "tier": "standard", "region": "cn"},
    # ── Fast occidental ────────────────────────────────────────────────────
    "anthropic/claude-haiku-3-5":       {"label": "Claude Haiku 3.5",       "tier": "fast", "region": "west"},
    "openai/gpt-4.1-nano":              {"label": "GPT-4.1 Nano",           "tier": "fast", "region": "west"},
    "openai/gpt-4.1-mini":              {"label": "GPT-4.1 Mini",           "tier": "fast", "region": "west"},
    "openai/gpt-5-nano":                {"label": "GPT-5 Nano",             "tier": "fast", "region": "west"},
    "openai/gpt-5.4-nano":              {"label": "GPT-5.4 Nano",           "tier": "fast", "region": "west"},
    "google/gemini-2.0-flash-lite-001": {"label": "Gemini 2.0 Flash Lite",  "tier": "fast", "region": "west"},
    "meta-llama/llama-3.3-70b-instruct":{"label": "Llama 3.3 70B",         "tier": "fast", "region": "west"},
    # ── Fast Chine ─────────────────────────────────────────────────────────
    "deepseek/deepseek-r1-0528-qwen3-8b": {"label": "DeepSeek R1 × Qwen3 8B", "tier": "fast", "region": "cn"},
    "z-ai/glm-4.5-air":                 {"label": "GLM 4.5 Air",            "tier": "fast", "region": "cn"},
}

# Alias runtime → clé canonique (UI / agent_models.json)
AGENT_ID_ALIASES: dict[str, str] = {
    "coo_agent": "coo",
    "spec_agent": "spec",
    "pm_agent": "pm",
    "qa_agent": "qa",
    "content_agent": "content",
    "brainstorm_agent": "brainstorm",
    "hardware_agent": "hardware",
    "marketing_agent": "marketing",
    "dev_app_agent": "dev_app",
    "dev_gaming_agent": "dev_gaming",
    "embedded_dev_agent": "embedded_dev",
    "game_director_agent": "game_director",
    "game_dir": "game_director",
    "dev_game": "dev_gaming",
    "rnd_center": "rnd_agent",
    "embedded": "embedded_dev",
    "secretary_agent": "secretary",
    "admin_agent": "secretary",
    "dev_backend_agent": "dev_backend",
    "backend_agent": "dev_backend",
    "level_designer_agent": "level_designer",
    "narrative_designer": "level_designer",
    "controller_agent": "controller",
    "financial_controller": "controller",
    "analyst_business_agent": "analyst_business",
    "business_analyst": "analyst_business",
    "analyst_data_agent": "analyst_data",
    "data_analyst": "analyst_data",
}

# Tier par défaut pour chaque agent (mode AUTO)
AGENT_TIERS: dict[str, str] = {
    "coo":           "premium",
    "spec":          "premium",
    "brainstorm":    "premium",
    "game_director": "premium",
    "rnd_agent":     "premium",
    "qa":            "standard",
    "dev_app":       "standard",
    "dev_gaming":    "standard",
    "marketing":     "standard",
    "hardware":      "standard",
    "embedded_dev":  "standard",
    "content":       "standard",
    "pm":               "fast",
    "accounting":       "fast",
    "secretary":        "fast",
    "controller":       "fast",
    "dev_backend":      "standard",
    "level_designer":   "standard",
    "analyst_business": "standard",
    "analyst_data":     "standard",
}

# Modèle par défaut par tier
TIER_DEFAULTS: dict[str, str] = {
    "premium":  "anthropic/claude-sonnet-4",
    "standard": "deepseek/deepseek-chat-v3.1",
    "fast":     "anthropic/claude-haiku-4-5",
}

_CONFIG_FILE = Path(os.getenv("HUB_REPO_PATH", "C:/Dev/ALUNA_HUB")) / "data" / "agent_models.json"


# ---------------------------------------------------------------------------
# Lecture / écriture de la config persistante
# ---------------------------------------------------------------------------

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


# ---------------------------------------------------------------------------
# API publique
# ---------------------------------------------------------------------------

def normalize_agent_id(agent_id: str) -> str:
    """Mappe coo_agent, spec_agent, etc. vers les clés de AGENT_TIERS."""
    key = agent_id.strip().lower()
    if key in AGENT_ID_ALIASES:
        return AGENT_ID_ALIASES[key]
    if key in AGENT_TIERS:
        return key
    if key.endswith("_agent"):
        short = key.removesuffix("_agent")
        if short in AGENT_TIERS:
            return short
    return key


# Noms d'affichage CrewAI / retry loop → clé Mem0 canonique
MEMORY_DISPLAY_ALIASES: dict[str, str] = {
    "devapp": "dev_app",
    "devgaming": "dev_gaming",
    "embeddeddev": "embedded_dev",
}


def memory_agent_id(agent_id: str) -> str:
    """Clé canonique Mem0 — alignée sur Paramètres / agent_models.json."""
    compact = agent_id.strip().lower().replace(" ", "").replace("-", "")
    if compact in MEMORY_DISPLAY_ALIASES:
        return MEMORY_DISPLAY_ALIASES[compact]
    return normalize_agent_id(agent_id)


def get_model_for_agent(agent_id: str) -> str:
    """
    Retourne le modèle OpenRouter à utiliser pour un agent donné.

    Priorité :
      1. Var d'env AGENT_MODEL_{AGENT_ID_UPPER}
      2. Fichier data/agent_models.json (choix dans Paramètres)
      3. Tier auto selon AGENT_TIERS
    """
    agent_id = normalize_agent_id(agent_id)

    # 1. Var d'env spécifique à l'agent
    env_key = f"AGENT_MODEL_{agent_id.upper()}"
    env_val = os.getenv(env_key, "").strip()
    if env_val:
        return env_val

    # 2. Choix explicite dans Paramètres (data/agent_models.json)
    file_config = _load_config()
    if agent_id in file_config and file_config[agent_id] != "auto":
        return file_config[agent_id]

    # 3. Mode Auto → tier de l'agent (premium / standard / fast)
    tier = AGENT_TIERS.get(agent_id, "standard")
    return TIER_DEFAULTS.get(tier, TIER_DEFAULTS["standard"])


def get_all_agent_models() -> list[dict[str, Any]]:
    """Retourne la config complète pour tous les agents (pour le Hub)."""
    file_config = _load_config()
    agents = []
    for agent_id, tier in AGENT_TIERS.items():
        stored = file_config.get(agent_id, "auto")
        resolved = get_model_for_agent(agent_id)
        clean = resolved.replace("openrouter/", "")
        agents.append({
            "agent_id": agent_id,
            "tier": tier,
            "configured": stored,       # "auto" ou nom de modèle
            "resolved": resolved,        # modèle effectivement utilisé
            "label": AVAILABLE_MODELS.get(clean, {}).get("label", clean),
        })
    return agents


def set_agent_model(agent_id: str, model: str) -> None:
    """
    Définit le modèle pour un agent. Utiliser "auto" pour revenir au mode automatique.
    """
    agent_id = normalize_agent_id(agent_id)
    config = _load_config()
    if model == "auto":
        config.pop(agent_id, None)
    else:
        config[agent_id] = model
    _save_config(config)
    logger.info("agent_models: %s → %s", agent_id, model)
