"""Composio direct action execution."""

from __future__ import annotations

import logging
from typing import Any

from skills.skill_composio_client import (
    _create_session,
    _get_composio_client,
    _toolkit_from_action,
    _unwrap_execute_response,
)

logger = logging.getLogger(__name__)


def composio_execute(
    action: str,
    params: dict[str, Any],
    user_id: str = "alnua_default",
) -> dict[str, Any]:
    """
    Exécute une action Composio directement (sans passer par un agent).

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
