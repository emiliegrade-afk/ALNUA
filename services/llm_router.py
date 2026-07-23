"""
services/llm_router.py — Routeur LLM dynamique adapté à ALNUA Hub.

Inspiré de NadirClaw (github.com/doramirdor/nadirclaw) :
Route chaque appel vers le tier optimal (fast/standard/premium)
selon la complexité mesurée dynamiquement plutôt que statiquement.

Usage :
    from services.llm_router import route_to_model, complexity_score

    model = route_to_model(agent_id="dev_app", prompt=user_prompt, method="review_code")
    # → "anthropic/claude-3.5-haiku" ou upgrade/downgrade selon la complexité
"""

from __future__ import annotations

import re
from typing import Any

from config.agent_models import AGENT_TIERS

# ---------------------------------------------------------------------------
# Seuils de complexité
# ---------------------------------------------------------------------------

# Tokens approximatifs (1 token ≈ 4 chars)
_LOW_CHAR_THRESHOLD = 200      # < 200 chars → potentiellement downgradeable
_HIGH_CHAR_THRESHOLD = 2000    # > 2000 chars → potentiellement upgradeable

# Méthodes qui méritent toujours le tier supérieur
_ALWAYS_UPGRADE_METHODS = {
    "market_analysis",
    "strategic_brief",
    "game_concept",
    "write_gdd",
    "research",
    "prototype_spec",
    "debate_spec",          # adversarial spec — toujours premium
    "monthly_report",
}

# Méthodes simples qui peuvent être dégradées
_ALLOW_DOWNGRADE_METHODS = {
    "sql_query",
    "anomaly_report",
    "triage_emails",
    "llm_cost_alert",
    "bom_lookup",
    "hardware_spec",
    "firmware_task",
}

# Signaux de complexité dans le prompt (regex)
_COMPLEXITY_SIGNALS = [
    r"compare[zr]?\s+\w+\s+(avec|et|vs)",   # comparaison multi-entités
    r"(analyse|analyser)\s+.*\s+et\s+",       # analyse multi-axe
    r"(stratégi|strateg)",                    # réflexion stratégique
    r"(\d+)\s+(concurrent|alternative|option)",  # multi-options
    r"(architecture|système|pipeline)\s+complet", # design système
    r"(risk|risque|menace|threat)",           # analyse de risque
]
_COMPILED_SIGNALS = [re.compile(p, re.IGNORECASE) for p in _COMPLEXITY_SIGNALS]

# Tiers ordonnés
_TIER_ORDER = ["fast", "standard", "premium"]


def complexity_score(prompt: str, method_name: str = "") -> int:
    """
    Score de 0 à 10 :
    - 0-3 : simple (fast suffisant)
    - 4-6 : moyen (standard)
    - 7-10 : complexe (premium recommandé)
    """
    score = 0

    # Longueur du prompt
    n = len(prompt)
    if n > _HIGH_CHAR_THRESHOLD:
        score += 3
    elif n > 800:
        score += 1
    elif n < _LOW_CHAR_THRESHOLD:
        score -= 1

    # Signaux de complexité dans le texte
    signal_hits = sum(1 for rx in _COMPILED_SIGNALS if rx.search(prompt))
    score += min(signal_hits * 2, 4)

    # Méthode connue
    if method_name in _ALWAYS_UPGRADE_METHODS:
        score += 3
    elif method_name in _ALLOW_DOWNGRADE_METHODS:
        score -= 1

    # Ponctuation : JSON complexes, listes d'options, tableaux
    if prompt.count("{") > 3:
        score += 1
    if prompt.count("\n") > 15:
        score += 1

    return max(0, min(score, 10))


def _tier_for_score(score: int) -> str:
    if score >= 7:
        return "premium"
    if score >= 4:
        return "standard"
    return "fast"


def _upgrade_tier(tier: str) -> str:
    idx = _TIER_ORDER.index(tier)
    return _TIER_ORDER[min(idx + 1, len(_TIER_ORDER) - 1)]


def _downgrade_tier(tier: str) -> str:
    idx = _TIER_ORDER.index(tier)
    return _TIER_ORDER[max(idx - 1, 0)]


def route_to_model(
    agent_id: str,
    prompt: str,
    method_name: str = "",
    force_tier: str | None = None,
) -> str:
    """
    Retourne le model slug OpenRouter optimal pour cet appel.

    Args:
        agent_id:    Identifiant agent (ex: "dev_app", "analyst_data")
        prompt:      Contenu du prompt utilisateur (pour mesurer la complexité)
        method_name: Nom de la méthode appelée (signal additionnel)
        force_tier:  Forcer un tier manuellement ("fast" | "standard" | "premium")

    Returns:
        Model slug OpenRouter (ex: "anthropic/claude-3.5-haiku")
    """
    from config.agent_models import TIER_MODELS

    # Tier de base configuré statiquement pour cet agent
    static_tier = AGENT_TIERS.get(agent_id, "standard")

    if force_tier and force_tier in _TIER_ORDER:
        target_tier = force_tier
    else:
        score = complexity_score(prompt, method_name)
        dynamic_tier = _tier_for_score(score)

        # Politique : on peut monter d'un cran mais pas descendre sous le tier statique
        # (on ne dégrade jamais un agent premium vers fast, par exemple)
        static_idx = _TIER_ORDER.index(static_tier)
        dynamic_idx = _TIER_ORDER.index(dynamic_tier)

        if dynamic_idx > static_idx:
            # Upgrade autorisé si le prompt est vraiment complexe
            target_tier = dynamic_tier
        else:
            # Downgrade bloqué — on reste au minimum au tier statique
            target_tier = static_tier

    return TIER_MODELS.get(target_tier, TIER_MODELS["standard"])


def routing_report(agent_id: str, prompt: str, method_name: str = "") -> dict[str, Any]:
    """
    Debug : retourne le rapport complet de routage pour un appel donné.
    Utilisé par Rémi (Contrôleur) pour auditer les décisions de routage.
    """
    from config.agent_models import TIER_MODELS

    static_tier = AGENT_TIERS.get(agent_id, "standard")
    score = complexity_score(prompt, method_name)
    dynamic_tier = _tier_for_score(score)
    routed_model = route_to_model(agent_id, prompt, method_name)

    return {
        "agent_id": agent_id,
        "method": method_name,
        "static_tier": static_tier,
        "complexity_score": score,
        "dynamic_tier_suggestion": dynamic_tier,
        "final_tier": next(
            (t for t, m in TIER_MODELS.items() if m == routed_model), "unknown"
        ),
        "routed_model": routed_model,
        "prompt_length_chars": len(prompt),
        "upgrade_triggered": dynamic_tier != static_tier and _TIER_ORDER.index(dynamic_tier) > _TIER_ORDER.index(static_tier),
    }
