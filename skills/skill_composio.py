"""
skill_composio.py

Gateway OAuth centralisée via Composio — donne aux agents ALNUA l'accès
à 250+ APIs externes (Gmail, Calendar, Notion, Stripe, Discord, GitHub...)
sans gérer le OAuth manuellement.

Usage dans un agent CrewAI :
    from skills.skill_composio import get_composio_tools, composio_execute

    tools = get_composio_tools(
        apps=["GMAIL", "GOOGLECALENDAR", "NOTION"],
        user_id="alnua_coo"
    )

    result = composio_execute(
        action="GMAIL_SEND_EMAIL",
        params={"to": "test@example.com", "subject": "Hello", "body": "..."},
        user_id="alnua_coo"
    )
"""

from __future__ import annotations

import logging

from config.settings import get_settings

from skills.skill_composio_constants import AGENT_APP_MAP  # noqa: F401 — re-export
from skills.skill_composio_execute import composio_execute  # noqa: F401 — re-export
from skills.skill_composio_oauth import (  # noqa: F401 — re-export
    disconnect_toolkit,
    get_gmail_profile_email,
    get_oauth_link,
    has_active_connection,
    list_connected_apps,
)

logger = logging.getLogger(__name__)


def _get_composio_api_key() -> str:
    """Read Composio key from Settings (Pydantic loads .env reliably)."""
    return get_settings().composio_api_key.strip()


from skills.skill_composio_client import (  # noqa: E402 — after _get_composio_api_key
    _create_session,
    _get_composio_client,
    _toolkit_from_action,
)


def get_composio_tools(
    apps: list[str] | None = None,
    agent_name: str | None = None,
    actions: list[str] | None = None,
    user_id: str = "alnua_default",
) -> list:
    """
    Retourne une liste de CrewAI tools Composio pour les apps demandées.
    """
    try:
        composio = _get_composio_client(with_crewai_provider=True)

        target_apps = apps
        if target_apps is None and agent_name:
            target_apps = AGENT_APP_MAP.get(agent_name, [])
        if not target_apps and actions:
            target_apps = sorted({_toolkit_from_action(action).upper() for action in actions})
        if not target_apps:
            logger.warning("get_composio_tools appelé sans apps ni actions — retourne []")
            return []

        session = _create_session(composio, user_id=user_id, toolkits=target_apps)
        tools = session.tools()

        logger.info(
            "Composio: %s tools chargés pour user=%s apps=%s",
            len(tools),
            user_id,
            target_apps,
        )
        return tools

    except Exception as e:
        logger.error("Erreur Composio get_composio_tools: %s", e)
        return []


__all__ = [
    "AGENT_APP_MAP",
    "composio_execute",
    "disconnect_toolkit",
    "get_composio_tools",
    "get_gmail_profile_email",
    "get_oauth_link",
    "has_active_connection",
    "list_connected_apps",
]
