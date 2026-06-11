"""
skill_composio.py

Gateway OAuth centralisée via Composio — donne aux agents ALNUA l'accès
à 250+ APIs externes (Gmail, Calendar, Notion, Stripe, Discord, GitHub...)
sans gérer le OAuth manuellement.

Usage dans un agent CrewAI :
    from skills.skill_composio import get_composio_tools, composio_execute

    # Obtenir des tools pour des apps spécifiques
    tools = get_composio_tools(
        apps=["GMAIL", "GOOGLECALENDAR", "NOTION"],
        user_id="alnua_coo"
    )

    # Ou exécuter une action directement
    result = composio_execute(
        action="GMAIL_SEND_EMAIL",
        params={"to": "test@example.com", "subject": "Hello", "body": "..."},
        user_id="alnua_coo"
    )
"""

from __future__ import annotations

import logging
import os
from typing import Any

logger = logging.getLogger(__name__)

# Apps disponibles par rôle agent — limite à ce dont chaque agent a besoin
AGENT_APP_MAP: dict[str, list[str]] = {
    "coo_agent": [
        "GMAIL", "GOOGLECALENDAR", "NOTION", "SLACK",
        "GITHUB", "GOOGLESHEETS",
    ],
    "pm_agent": [
        "GITHUB", "NOTION", "GOOGLESHEETS", "LINEAR",
    ],
    "dev_app_agent": [
        "GITHUB", "VERCEL", "SUPABASE",
    ],
    "marketing_agent": [
        "TWITTER", "INSTAGRAM", "LINKEDIN", "MAILCHIMP",
        "NOTION", "GOOGLEDRIVE",
    ],
    "content_agent": [
        "NOTION", "GOOGLEDOCS", "WORDPRESS", "TWITTER",
    ],
    "qa_agent": [
        "GITHUB", "SLACK",
    ],
    "hardware_agent": [
        "NOTION", "GOOGLEDRIVE",
    ],
    "game_director_agent": [
        "DISCORD", "NOTION",
    ],
    "spec_agent": [
        "NOTION", "GOOGLEDOCS", "GITHUB",
    ],
}


def _get_composio_client():
    """Initialise le client Composio (lazy)."""
    api_key = os.getenv("COMPOSIO_API_KEY")
    if not api_key:
        raise RuntimeError(
            "COMPOSIO_API_KEY manquante dans .env — "
            "Crée un compte sur https://dashboard.composio.dev et copie ta clé."
        )
    try:
        from composio import Composio
        from composio_crewai import CrewAIProvider
        return Composio(api_key=api_key, provider=CrewAIProvider())
    except ImportError as e:
        raise ImportError(
            f"Composio non installé : {e}\n"
            "Lance : pip install composio composio_crewai"
        ) from e


def get_composio_tools(
    apps: list[str] | None = None,
    agent_name: str | None = None,
    actions: list[str] | None = None,
    user_id: str = "alnua_default",
) -> list:
    """
    Retourne une liste de CrewAI tools Composio pour les apps demandées.

    Args:
        apps: Liste d'apps ex. ["GMAIL", "GOOGLECALENDAR"]
              Si None, utilise le mapping par agent_name.
        agent_name: Nom de l'agent (ex. "coo_agent") pour charger ses apps par défaut.
        actions: Liste d'actions spécifiques ex. ["GMAIL_SEND_EMAIL"]
                 Prioritaire sur apps si fourni.
        user_id: Identifiant utilisateur pour la session OAuth.

    Returns:
        Liste de BaseTool CrewAI prêts à injecter dans un Agent.
    """
    try:
        composio = _get_composio_client()

        # Résoudre la liste d'apps
        target_apps = apps
        if target_apps is None and agent_name:
            target_apps = AGENT_APP_MAP.get(agent_name, [])
        if not target_apps and not actions:
            logger.warning("get_composio_tools appelé sans apps ni actions — retourne []")
            return []

        session = composio.create(user_id=user_id)

        if actions:
            tools = session.tools(actions=actions)
        else:
            tools = session.tools(apps=target_apps)

        logger.info(
            f"Composio: {len(tools)} tools chargés pour user={user_id} "
            f"apps={target_apps or 'via actions'}"
        )
        return tools

    except Exception as e:
        logger.error(f"Erreur Composio get_composio_tools: {e}")
        return []


def composio_execute(
    action: str,
    params: dict[str, Any],
    user_id: str = "alnua_default",
) -> dict[str, Any]:
    """
    Exécute une action Composio directement (sans passer par un agent).

    Args:
        action: Identifiant action ex. "GMAIL_SEND_EMAIL", "GOOGLECALENDAR_CREATE_EVENT"
        params: Paramètres de l'action
        user_id: Session utilisateur

    Returns:
        {"success": bool, "data": ..., "error": str | None}

    Exemples d'actions utiles :
        GMAIL_SEND_EMAIL — envoyer un mail
        GOOGLECALENDAR_CREATE_EVENT — créer un événement
        NOTION_CREATE_PAGE — créer une page Notion
        GITHUB_CREATE_ISSUE — créer une issue GitHub
        SLACK_SEND_MESSAGE — envoyer un message Slack
    """
    try:
        from composio import Composio

        api_key = os.getenv("COMPOSIO_API_KEY")
        composio_client = Composio(api_key=api_key)
        session = composio_client.create(user_id=user_id)
        result = session.execute(action=action, params=params)
        return {"success": True, "data": result, "error": None}
    except Exception as e:
        logger.error(f"Erreur composio_execute({action}): {e}")
        return {"success": False, "data": None, "error": str(e)}


_STALE_CONNECTION_STATUSES = frozenset(
    {"EXPIRED", "FAILED", "REVOKED", "INITIALIZING", "INITIATED"},
)


def _purge_stale_connections(
    composio_client: Any,
    *,
    user_id: str,
    toolkit: str,
) -> None:
    """Drop abandoned OAuth attempts before creating a fresh link."""
    connections = composio_client.connected_accounts.list(
        user_ids=[user_id],
        toolkit_slugs=[toolkit],
    )
    for connection in connections.items:
        if connection.status not in _STALE_CONNECTION_STATUSES:
            continue
        try:
            composio_client.connected_accounts.delete(nanoid=connection.id)
        except Exception as exc:
            logger.warning(
                "Could not delete stale Composio connection %s: %s",
                connection.id,
                exc,
            )


def get_oauth_link(
    app: str,
    user_id: str = "alnua_default",
    redirect_url: str | None = None,
) -> str:
    """
    Génère un lien OAuth pour connecter une app à un user_id.
    À envoyer via Telegram au COO pour autoriser une nouvelle app.

    Args:
        app: Nom de l'app ex. "GMAIL", "NOTION"
        user_id: Session utilisateur
        redirect_url: URL de redirection après auth (optionnel)

    Returns:
        URL OAuth à ouvrir dans le navigateur
    """
    try:
        from composio import Composio

        api_key = os.getenv("COMPOSIO_API_KEY")
        composio_client = Composio(api_key=api_key)
        toolkit = app.lower()
        connections = composio_client.connected_accounts.list(
            user_ids=[user_id],
            toolkit_slugs=[toolkit],
            statuses=["ACTIVE"],
        )
        if connections.items:
            active = connections.items[0]
            return f"{app} est déjà connecté ✅ (depuis {active.created_at})"

        _purge_stale_connections(
            composio_client, user_id=user_id, toolkit=toolkit,
        )
        auth_config_id = composio_client.toolkits._get_auth_config_id(
            toolkit=toolkit,
        )
        request = composio_client.connected_accounts.link(
            user_id=user_id,
            auth_config_id=auth_config_id,
            callback_url=redirect_url,
        )
        return request.redirect_url or ""
    except Exception as e:
        logger.error(f"Erreur get_oauth_link({app}): {e}")
        return f"Erreur: {e}"


def list_connected_apps(user_id: str = "alnua_default") -> list[dict]:
    """
    Liste les apps connectées (OAuth validé) pour un user_id.

    Returns:
        [{"app": "GMAIL", "status": "active", "connected_at": "..."}, ...]
    """
    try:
        from composio import Composio

        api_key = os.getenv("COMPOSIO_API_KEY")
        composio_client = Composio(api_key=api_key)
        connections = composio_client.connected_accounts.list(
            user_ids=[user_id],
            statuses=["ACTIVE"],
        )
        return [
            {
                "app": (c.toolkit.slug if c.toolkit else "unknown").upper(),
                "status": c.status,
                "connected_at": str(c.created_at),
            }
            for c in connections.items
        ]
    except Exception as e:
        logger.error(f"Erreur list_connected_apps: {e}")
        return []
