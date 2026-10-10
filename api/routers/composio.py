"""Auto-split from api/main.py — composio routes."""

from __future__ import annotations

from api.route_common import *  # noqa: F403

router = APIRouter()


@router.get("/composio/apps")
async def list_composio_apps(user_id: str | None = None):
    """Liste les apps connectées via Composio OAuth."""
    from services.secretary_composio import composio_user_id, list_ceo_connections

    uid = user_id or composio_user_id()
    return list_ceo_connections() if uid == composio_user_id() else __import__(
        "skills.skill_composio", fromlist=["list_connected_apps"]
    ).list_connected_apps(user_id=uid)


@router.post("/composio/connect/{app_name}")
async def connect_composio_app(app_name: str, user_id: str | None = None):
    """Génère un lien OAuth pour connecter une app. Renvoie le lien à ouvrir."""
    from services.secretary_composio import (
        composio_user_id,
        get_oauth_link_for_ceo,
        split_oauth_reply,
    )
    from skills.skill_composio import get_oauth_link

    uid = user_id or composio_user_id()
    if uid == composio_user_id():
        link = get_oauth_link_for_ceo(app_name)
    else:
        link = get_oauth_link(app=app_name.upper(), user_id=uid)
    url, hint = split_oauth_reply(link)
    return {"app": app_name, "oauth_url": url or link, "hint": hint}


