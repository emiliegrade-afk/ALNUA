"""Auto-split from api/main.py — composio routes."""

from __future__ import annotations

from api.route_common import *  # noqa: F403

router = APIRouter()


@router.get("/composio/apps")
async def list_composio_apps(user_id: str = "alnua_coo"):
    """Liste les apps connectées via Composio OAuth."""
    from skills.skill_composio import list_connected_apps

    return list_connected_apps(user_id=user_id)


@router.post("/composio/connect/{app_name}")
async def connect_composio_app(app_name: str, user_id: str = "alnua_coo"):
    """Génère un lien OAuth pour connecter une app. Renvoie le lien à ouvrir."""
    from skills.skill_composio import get_oauth_link

    link = get_oauth_link(app=app_name.upper(), user_id=user_id)
    return {"app": app_name, "oauth_url": link}


