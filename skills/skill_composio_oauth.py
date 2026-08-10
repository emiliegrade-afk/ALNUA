"""Composio OAuth link generation and connection management."""

from __future__ import annotations

import logging

from skills.skill_composio_client import _get_composio_client
from skills.skill_composio_constants import _STALE_CONNECTION_STATUSES
from skills.skill_composio_execute import composio_execute

logger = logging.getLogger(__name__)


def _purge_stale_connections(
    composio_client,
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


def disconnect_toolkit(user_id: str, toolkit: str) -> int:
    """Revoke all Composio OAuth sessions for a toolkit. Returns count removed."""
    removed = 0
    try:
        composio_client = _get_composio_client()
        connections = composio_client.connected_accounts.list(
            user_ids=[user_id],
            toolkit_slugs=[toolkit.lower()],
        )
        for connection in connections.items:
            try:
                composio_client.connected_accounts.delete(nanoid=connection.id)
                removed += 1
            except Exception as exc:
                logger.warning("disconnect_toolkit %s: %s", connection.id, exc)
    except Exception as exc:
        logger.error("disconnect_toolkit(%s, %s): %s", user_id, toolkit, exc)
    return removed


def get_gmail_profile_email(user_id: str) -> str | None:
    """Return the email address of the active Gmail OAuth session, if any."""
    if not has_active_connection(user_id, "gmail"):
        return None
    result = composio_execute("GMAIL_GET_PROFILE", {}, user_id=user_id)
    if not result.get("success"):
        return None
    data = result.get("data") or {}
    if isinstance(data, dict) and "data" in data:
        data = data["data"]
    if isinstance(data, dict):
        email = data.get("emailAddress") or data.get("email")
        return str(email).strip() if email else None
    return None


def list_connected_apps(user_id: str = "alnua_default") -> list[dict]:
    """
    Liste les apps connectées (OAuth validé) pour un user_id.
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
