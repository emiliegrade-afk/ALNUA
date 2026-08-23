"""Auto-split from api/main.py — settings routes."""

from __future__ import annotations

from api.route_common import *  # noqa: F403

router = APIRouter()



class AgentModelUpdate(BaseModel):
    agent_id: str
    model: str  # nom de modèle OpenRouter ou "auto"


@router.get("/settings/coding")
def settings_coding_info() -> dict[str, Any]:
    """Pipeline de code : backend + modèle dev_app (source unique Paramètres)."""
    from config.agent_models import CODING_AGENT_IDS, get_coding_model_for_agent
    from services.coding_pipeline import get_coding_config

    get_coding_config.cache_clear()
    cfg = get_coding_config()
    return {
        "backend": cfg.backend,
        "coding_agents": sorted(CODING_AGENT_IDS),
        "dev_app_model": get_coding_model_for_agent("dev_app"),
        "aider_model_override": cfg.aider_model or None,
        "note": "Le modèle de code = Paramètres (/settings) pour chaque agent dev. Pas de choix automatique Aider.",
    }


@router.get("/settings/models")
def settings_get_models() -> list[dict]:
    """Retourne la config modèle de tous les agents."""
    from config.agent_models import get_all_agent_models
    return get_all_agent_models()


@router.get("/settings/models/available")
def settings_available_models() -> dict:
    """Catalogue modèles classés par usage (code, chat, reasoning…)."""
    from config.agent_models import (
        MODEL_CATEGORIES,
        MODEL_CATEGORY_ORDER,
        TIER_DEFAULTS,
        get_enriched_available_models,
    )
    return {
        "models": get_enriched_available_models(),
        "categories": MODEL_CATEGORIES,
        "category_order": MODEL_CATEGORY_ORDER,
        "tier_defaults": TIER_DEFAULTS,
    }


@router.post("/settings/models")
def settings_set_model(body: AgentModelUpdate) -> dict[str, str]:
    """Définit le modèle pour un agent. Passer model='auto' pour reset."""
    from config.agent_models import (
        AGENT_TIERS,
        AVAILABLE_MODELS,
        normalize_agent_id,
        set_agent_model,
    )

    agent_id = normalize_agent_id(body.agent_id)
    if agent_id not in AGENT_TIERS:
        raise HTTPException(status_code=400, detail=f"Agent inconnu : {body.agent_id}")
    if body.model != "auto" and body.model not in AVAILABLE_MODELS:
        raise HTTPException(status_code=400, detail=f"Modèle inconnu : {body.model}")

    set_agent_model(agent_id, body.model)
    return {"ok": f"{agent_id} → {body.model}"}


@router.post("/settings/models/reset")
def settings_reset_models() -> dict[str, str]:
    """Remet tous les agents en mode auto."""
    from config.agent_models import _CONFIG_FILE
    if _CONFIG_FILE.exists():
        _CONFIG_FILE.unlink()
    return {"ok": "Tous les agents repassés en mode auto"}


class ConnectivityUpdate(BaseModel):
    enabled: bool
    fallback_on_credit: bool
    base_url: str
    model: str
    api_key: str = ""


@router.get("/settings/llm-connectivity")
def settings_llm_connectivity() -> dict[str, Any]:
    """État du fallback LLM local (clé API jamais renvoyée en clair)."""
    from services.local_llm import get_local_llm_config, local_llm_available

    cfg = get_local_llm_config()
    return {
        "enabled": bool(cfg.get("enabled")),
        "fallback_on_credit": bool(cfg.get("fallback_on_credit", True)),
        "base_url": cfg.get("base_url", ""),
        "model": cfg.get("model", ""),
        "api_key_set": bool((cfg.get("api_key") or "").strip()),
        "available": local_llm_available(),
    }


@router.post("/settings/llm-connectivity")
def settings_update_llm_connectivity(body: ConnectivityUpdate) -> dict[str, str]:
    """Enregistre la config locale. api_key vide = conserver la clé existante."""
    from services.local_llm import save_local_llm_config

    api_key = body.api_key.strip() or None
    save_local_llm_config(
        {
            "enabled": body.enabled,
            "fallback_on_credit": body.fallback_on_credit,
            "base_url": body.base_url.strip(),
            "model": body.model.strip(),
        },
        api_key=api_key,
    )
    return {"ok": "Connectivité IA mise à jour"}


@router.post("/settings/llm-connectivity/test")
def settings_test_llm_connectivity() -> dict[str, Any]:
    """Test de connectivité au LLM local (max_tokens=1)."""
    from services.local_llm import ping_local_llm

    return ping_local_llm()


