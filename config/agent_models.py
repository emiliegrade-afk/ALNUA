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
    "google/gemma-4-31b-it":            {"label": "Gemma 4 31B",            "tier": "premium", "region": "west", "category": "code"},
    "google/gemma-4-26b-a4b-it":        {"label": "Gemma 4 26B A4B",        "tier": "standard", "region": "west", "category": "reasoning"},
    "x-ai/grok-4.3":                      {"label": "Grok 4.3",                 "tier": "premium", "region": "west"},
    # ── Premium Chine — raisonnement profond, agents ───────────────────────
    "deepseek/deepseek-r1-0528":        {"label": "DeepSeek R1 0528",       "tier": "premium", "region": "cn"},
    "moonshotai/kimi-k2.6":             {"label": "Kimi K2.6",              "tier": "premium", "region": "cn"},
    "moonshotai/kimi-k2.7-code":        {"label": "Kimi K2.7 Code",         "tier": "premium", "region": "cn"},
    "z-ai/glm-4.6":                     {"label": "GLM 4.6",                "tier": "premium", "region": "cn"},
    "z-ai/glm-5":                       {"label": "GLM 5",                  "tier": "premium", "region": "cn"},
    "z-ai/glm-5.1":                     {"label": "GLM 5.1",                "tier": "premium", "region": "cn"},
    "z-ai/glm-5.2":                     {"label": "GLM 5.2 (Z.ai)",         "tier": "premium", "region": "cn", "category": "reasoning"},
    # ── Premium occidental — Mistral & NVIDIA ─────────────────────────────
    "mistralai/mistral-large-2512":     {"label": "Mistral Large 3",        "tier": "premium", "region": "west"},
    "nvidia/nemotron-3-ultra-550b-a55b":{"label": "Nemotron 3 Ultra 550B","tier": "premium", "region": "west"},
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
    "minimax/minimax-m3":               {"label": "MiniMax 3 (M3)",         "tier": "premium", "region": "cn", "category": "reasoning"},
    # ── Standard occidental — Mistral & NVIDIA ─────────────────────────────
    "mistralai/mistral-medium-3-5":     {"label": "Mistral Medium 3.5",     "tier": "standard", "region": "west"},
    "mistralai/mistral-small-2603":     {"label": "Mistral Small 4",        "tier": "standard", "region": "west"},
    "mistralai/codestral-2508":         {"label": "Codestral 2508",         "tier": "standard", "region": "west"},
    "mistralai/devstral-2512":          {"label": "Devstral 2",             "tier": "standard", "region": "west"},
    "nvidia/nemotron-3-super-120b-a12b":{"label": "Nemotron 3 Super 120B","tier": "standard", "region": "west"},
    "nvidia/llama-3.3-nemotron-super-49b-v1.5": {"label": "Nemotron Super 49B", "tier": "standard", "region": "west"},
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
    "nvidia/nemotron-3-nano-30b-a3b":   {"label": "Nemotron 3 Nano 30B",  "tier": "fast", "region": "west"},
    "mistralai/ministral-3b-2512":      {"label": "Ministral 3 3B",         "tier": "fast", "region": "west"},
    # ── Fast Chine ─────────────────────────────────────────────────────────
    "deepseek/deepseek-r1-0528-qwen3-8b": {"label": "DeepSeek R1 × Qwen3 8B", "tier": "fast", "region": "cn"},
    "z-ai/glm-4.5-air":                 {"label": "GLM 4.5 Air",            "tier": "fast", "region": "cn"},
    # ── Non censuré (OpenRouter — créatif, peu de refus) ───────────────────
    "x-ai/grok-3":                      {"label": "Grok 3",                   "tier": "premium", "region": "west", "category": "uncensored"},
    "x-ai/grok-3-mini":                 {"label": "Grok 3 Mini",              "tier": "standard", "region": "west", "category": "uncensored"},
    "cognitivecomputations/dolphin-mistral-24b-venice-edition": {
        "label": "Dolphin Mistral 24B Venice", "tier": "standard", "region": "west", "category": "uncensored",
    },
    "cognitivecomputations/dolphin3.0-r1-mistral-24b": {
        "label": "Dolphin 3.0 R1 Mistral", "tier": "premium", "region": "west", "category": "uncensored",
    },
    "nousresearch/deephermes-3-mistral-24b-preview": {
        "label": "DeepHermes 3 Mistral 24B", "tier": "standard", "region": "west", "category": "uncensored",
    },
    "nousresearch/deephermes-3-llama-3-8b-preview": {
        "label": "DeepHermes 3 Llama 8B", "tier": "fast", "region": "west", "category": "uncensored",
    },
    "gryphe/mythomax-l2-13b":           {"label": "MythoMax L2 13B",          "tier": "fast", "region": "west", "category": "uncensored"},
    "sao10k/l3.1-euryale-70b":          {"label": "Euryale 70B",              "tier": "standard", "region": "west", "category": "uncensored"},
    "undi95/toppy-m-7b":                {"label": "Toppy M 7B",               "tier": "fast", "region": "west", "category": "uncensored"},
    "mistralai/mistral-nemo":           {"label": "Mistral Nemo (souple)",    "tier": "fast", "region": "west", "category": "uncensored"},
}

# Catégories UI — usage réel, pas géographie ni tier accidentel
MODEL_CATEGORIES: dict[str, str] = {
    "reasoning": "Raisonnement",
    "code": "Code",
    "chat": "Chat & rédaction",
    "fast": "Rapide & économique",
    "uncensored": "Non censuré",
}

MODEL_CATEGORY_ORDER: list[str] = [
    "reasoning",
    "code",
    "chat",
    "fast",
    "uncensored",
]

_AGENT_DISPLAY_FALLBACKS: dict[str, dict[str, str]] = {
    "rnd_dossier": {
        "display_name": "Pipeline R&D",
        "role_label": "Assemblage dossier",
        "department": "Pôle Innovation",
        "room": "rnd_lab",
    },
    "rnd_ceo": {
        "display_name": "Package CEO",
        "role_label": "Dossier → validation Emilie",
        "department": "Pôle Innovation",
        "room": "rnd_lab",
    },
    "rnd_committee": {
        "display_name": "Comité R&D",
        "role_label": "Revue comité",
        "department": "Pôle Innovation",
        "room": "rnd_lab",
    },
    "rnd_social": {
        "display_name": "Social R&D",
        "role_label": "Stratégie sociale dossier",
        "department": "Hub Business",
        "room": "comms_hub",
    },
    "rnd_visual": {
        "display_name": "Identité visuelle",
        "role_label": "Moodboard & brand dossier",
        "department": "Hub Business",
        "room": "comms_hub",
    },
    "rnd_product": {
        "display_name": "Fiche produit",
        "role_label": "Packaging produit R&D",
        "department": "Pôle App",
        "room": "app_office",
    },
}


def _infer_model_category(model_id: str, meta: dict[str, str]) -> str:
    """Classe un modèle par usage (code, chat, reasoning…) — pas par région."""
    if meta.get("category"):
        return meta["category"]
    mid = model_id.lower()
    uncensored_markers = (
        "dolphin", "mythomax", "euryale", "toppy", "venice", "deephermes",
        "grok", "mistral-nemo", "uncensored",
    )
    if any(m in mid for m in uncensored_markers):
        return "uncensored"
    code_markers = ("codex", "coder", "codestral", "devstral", "k2.7-code", "k2.7 code", "gemma-4-31b")
    if any(m in mid for m in code_markers):
        return "code"
    reasoning_markers = (
        "r1", "opus", "fable",
        "gpt-5-pro", "gpt-5.4-pro", "gpt-5.5-pro",
        "nemotron-3-ultra", "kimi-k2.6",
        "glm-5.1", "glm-5.2", "/glm-5",
        "minimax-m3", "gemma-4-26b",
    )
    if any(m in mid for m in reasoning_markers):
        return "reasoning"
    tier = meta.get("tier", "standard")
    if tier == "fast":
        return "fast"
    fast_markers = ("nano", "haiku", "flash-lite", "glm-4.5-air", "ministral", "3b-2512", "3b-")
    if any(m in mid for m in fast_markers):
        return "fast"
    return "chat"


def get_enriched_available_models() -> dict[str, dict[str, str]]:
    """Catalogue modèles avec category pour l'UI Paramètres."""
    out: dict[str, dict[str, str]] = {}
    for model_id, meta in AVAILABLE_MODELS.items():
        enriched = dict(meta)
        enriched["category"] = _infer_model_category(model_id, meta)
        out[model_id] = enriched
    return out


def _agent_display(agent_id: str) -> dict[str, str]:
    from config.agent_personas import ROOMS, get_persona

    persona = get_persona(agent_id)
    if persona:
        room_id = persona.get("room", "")
        department = ROOMS.get(room_id, {}).get("label", room_id or "ALNUA")
        return {
            "display_name": f"{persona['first_name']} {persona['last_name']}",
            "role_label": persona.get("role_label", agent_id),
            "department": department,
            "room": room_id,
        }
    fb = _AGENT_DISPLAY_FALLBACKS.get(agent_id)
    if fb:
        return fb
    return {
        "display_name": agent_id,
        "role_label": agent_id,
        "department": "ALNUA",
        "room": "",
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
    "dev_frontend_agent": "dev_frontend",
    "dev_integrator_agent": "dev_integrator",
    "content_app_agent": "content_app",
    "content_gaming_agent": "content_gaming",
    "content_robo_agent": "content_robo",
    "content_company_agent": "content_company",
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
    "dev_frontend":  "standard",
    "dev_integrator": "standard",
    "content_app":    "standard",
    "content_gaming": "standard",
    "content_robo":   "standard",
    "content_company": "standard",
    "coding_coach":  "fast",
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
    "rnd_dossier":      "premium",
    "rnd_ceo":          "premium",
    "rnd_committee":    "premium",
    "rnd_social":       "standard",
    "rnd_visual":       "standard",
    "rnd_product":      "standard",
}

# Agents whose Paramètres model also drives the autonomous coding pipeline (Hub Agent / Aider).
CODING_AGENT_IDS: frozenset[str] = frozenset(
    {"dev_app", "dev_backend", "dev_gaming", "embedded_dev", "dev_frontend", "dev_integrator"}
)

# Modèle par défaut par tier
TIER_DEFAULTS: dict[str, str] = {
    "premium":  "anthropic/claude-sonnet-4",
    "standard": "deepseek/deepseek-chat-v3.1",
    "fast":     "anthropic/claude-haiku-4-5",
}

from config.paths import get_hub_repo_path

_CONFIG_FILE = get_hub_repo_path() / "data" / "agent_models.json"


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


def get_coding_model_for_agent(agent_id: str) -> str:
    """
    Modèle pour le pipeline de code (Hub Agent / Aider).

    Une seule source de vérité : même résolution que get_model_for_agent.
    Le réglage Paramètres / data/agent_models.json s'applique au chat ET au code.
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
    agents = []
    for agent_id, tier in AGENT_TIERS.items():
        stored = file_config.get(agent_id, "auto")
        resolved = get_model_for_agent(agent_id)
        clean = resolved.replace("openrouter/", "")
        display = _agent_display(agent_id)
        agents.append({
            "agent_id": agent_id,
            "tier": tier,
            "configured": stored,
            "resolved": resolved,
            "label": get_enriched_available_models().get(clean, {}).get("label", clean),
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
