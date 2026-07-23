"""Plugin marketplace API."""

from __future__ import annotations

from api.route_common import *  # noqa: F403

from typing import Any

from services.plugin_loader import discover_plugins, list_plugins, load_plugin_agent

router = APIRouter()


@router.get("/plugins")
def get_plugins() -> list[dict[str, Any]]:
    return list_plugins()


@router.post("/plugins/{plugin_id}/run")
def run_plugin(plugin_id: str, body: dict[str, str]) -> dict[str, Any]:
    message = body.get("message", "").strip()
    if not message:
        raise HTTPException(status_code=400, detail="message requis")
    for manifest in discover_plugins():
        if manifest.id == plugin_id:
            agent_cls = load_plugin_agent(manifest)
            if not agent_cls:
                raise HTTPException(status_code=500, detail="Plugin agent non chargeable")
            agent = agent_cls()
            return agent.run(message)
    raise HTTPException(status_code=404, detail=f"Plugin {plugin_id} introuvable")
