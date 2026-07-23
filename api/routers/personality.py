"""Personality customization API — per-tenant agent tone."""

from __future__ import annotations

from api.route_common import *  # noqa: F403

from typing import Any

from agents.personalities import PersonalityOverrides, get_personality, set_personality
from models.tenant import DEFAULT_TENANT_ID

router = APIRouter()


@router.get("/personality")
def get_tenant_personality(tenant_id: str = DEFAULT_TENANT_ID) -> dict[str, Any]:
    overrides = get_personality(tenant_id)
    if not overrides:
        return {"tenant_id": tenant_id, "overrides": None}
    return {"tenant_id": tenant_id, "overrides": overrides.model_dump()}


@router.put("/personality")
def update_tenant_personality(
    body: PersonalityOverrides,
    tenant_id: str = DEFAULT_TENANT_ID,
) -> dict[str, Any]:
    set_personality(tenant_id, body)
    from services.personality_store import save_personality_to_db
    save_personality_to_db(tenant_id, body)
    return {"tenant_id": tenant_id, "overrides": body.model_dump(), "saved": True}
