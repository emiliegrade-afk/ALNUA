"""Auto-split from api/main.py — settings routes."""

from __future__ import annotations

from api.route_common import *  # noqa: F403

router = APIRouter()



class AgentModelUpdate(BaseModel):
    agent_id: str
    model: str  # nom de modèle OpenRouter ou "auto"


@router.get("/settings/models")
def settings_get_models() -> list[dict]:
    """Retourne la config modèle de tous les agents."""
    from config.agent_models import get_all_agent_models
    return get_all_agent_models()


@router.get("/settings/models/available")
def settings_available_models() -> dict:
    """Retourne la liste des modèles disponibles par tier."""
    from config.agent_models import AVAILABLE_MODELS, TIER_DEFAULTS
    return {"models": AVAILABLE_MODELS, "tier_defaults": TIER_DEFAULTS}


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


