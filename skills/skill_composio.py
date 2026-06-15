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
from typing import Any

from config.settings import get_settings

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
        "NOTION", "GOOGLEDRIVE", "GITHUB", "GOOGLESHEETS",
    ],
    "content_agent": [
        "NOTION", "GOOGLEDOCS", "GITHUB",
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


def _get_composio_api_key() -> str:
    """Read Composio key from Settings (Pydantic loads .env reliably)."""
    return get_settings().composio_api_key.strip()


def _get_composio_client(*, with_crewai_provider: bool = False):
    """Initialise le client Composio (lazy)."""
    api_key = _get_composio_api_key()
    if not api_key:
        raise RuntimeError(
            "COMPOSIO_API_KEY manquante dans .env — "
            "Crée un compte sur https://dashboard.composio.dev et copie ta clé."
        )
    try:
        from composio import Composio

        if with_crewai_provider:
            from composio_crewai import CrewAIProvider

            return Composio(api_key=api_key, provider=CrewAIProvider())
        return Composio(api_key=api_key)
    except ImportError as e:
        raise ImportError(
            f"Composio non installé : {e}\n"
            "Lance : pip install composio composio_crewai"
        ) from e


def _normalize_toolkits(names: list[str]) -> list[str]:
    return [name.lower() for name in names]


def _toolkit_from_action(action: str) -> str:
    return action.split("_", 1)[0].lower()


def _get_connected_accounts(
    composio_client: Any,
    *,
    user_id: str,
    toolkits: list[str] | None = None,
) -> dict[str, str]:
    """Map toolkit slug -> connected account id for active OAuth sessions."""
    connections = composio_client.connected_accounts.list(
        user_ids=[user_id],
        statuses=["ACTIVE"],
    )
    allowed = {toolkit.lower() for toolkit in toolkits} if toolkits else None
    mapping: dict[str, str] = {}
    for connection in connections.items:
        slug = (connection.toolkit.slug if connection.toolkit else "").lower()
        if not slug:
            continue
        if allowed is not None and slug not in allowed:
            continue
        mapping[slug] = connection.id
    return mapping


def _create_session(
    composio_client: Any,
    *,
    user_id: str,
    toolkits: list[str],
):
    normalized = _normalize_toolkits(toolkits)
    connected_accounts = _get_connected_accounts(
        composio_client,
        user_id=user_id,
        toolkits=normalized,
    )
    return composio_client.create(
        user_id=user_id,
        toolkits=normalized,
        connected_accounts=connected_accounts or None,
    )


def _unwrap_execute_response(result: Any) -> dict[str, Any]:
    """Normalize Composio v1 multi-execute payload to {success, data, error}."""
    payload = getattr(result, "data", None) or {}
    results = payload.get("results") if isinstance(payload, dict) else None
    if not results:
        error = getattr(result, "error", None)
        return {
            "success": not error,
            "data": payload if payload else None,
            "error": str(error) if error else None,
        }

    first = results[0]
    response = first.get("response") if isinstance(first, dict) else None
    if isinstance(response, dict) and response.get("successful"):
        return {"success": True, "data": response.get("data"), "error": None}

    error = None
    if isinstance(first, dict):
        error = first.get("error")
        if not error and isinstance(response, dict):
            error = response.get("error")
    error = error or getattr(result, "error", None) or "Composio action failed"
    return {"success": False, "data": None, "error": str(error)}


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
                 Utilisé pour déduire les toolkits si apps absent.
        user_id: Identifiant utilisateur pour la session OAuth.

    Returns:
        Liste de BaseTool CrewAI prêts à injecter dans un Agent.
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
    """
    try:
        composio_client = _get_composio_client()
        toolkit = _toolkit_from_action(action)
        session = _create_session(
            composio_client,
            user_id=user_id,
            toolkits=[toolkit],
        )
        result = session.execute(
            "COMPOSIO_MULTI_EXECUTE_TOOL",
            arguments={
                "tools": [{"tool_slug": action, "arguments": params}],
                "sync_response_to_workbench": False,
            },
        )
        return _unwrap_execute_response(result)
    except Exception as e:
        logger.error("Erreur composio_execute(%s): %s", action, e)
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
        composio_client = _get_composio_client()
        toolkit = app.lower()
        connections = composio_client.connected_accounts.list(
            user_ids=[user_id],
            toolkit_slugs=[toolkit],
            statuses=["ACTIVE"],
        )
        if connections.items:
            active = connections.items[0]
            return f"{app} est déjà connecté [OK] (depuis {active.created_at})"

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
        logger.error("Erreur get_oauth_link(%s): %s", app, e)
        return f"Erreur: {e}"


def has_active_connection(user_id: str, toolkit: str) -> bool:
    """Return True when Composio has an ACTIVE OAuth session for the toolkit."""
    try:
        composio_client = _get_composio_client()
        connections = composio_client.connected_accounts.list(
            user_ids=[user_id],
            toolkit_slugs=[toolkit.lower()],
            statuses=["ACTIVE"],
        )
        return bool(connections.items)
    except Exception as exc:
        logger.warning("has_active_connection(%s, %s): %s", user_id, toolkit, exc)
        return False


def list_connected_apps(user_id: str = "alnua_default") -> list[dict]:
    """
    Liste les apps connectées (OAuth validé) pour un user_id.

    Returns:
        [{"app": "GMAIL", "status": "active", "connected_at": "..."}, ...]
    """
    try:
        composio_client = _get_composio_client()
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
        logger.error("Erreur list_connected_apps: %s", e)
        return []
