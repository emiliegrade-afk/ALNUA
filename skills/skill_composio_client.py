"""Composio SDK client bootstrap and session helpers."""

from __future__ import annotations

from typing import Any


def _resolve_api_key() -> str:
    """Delegate to façade so tests can monkeypatch ``skill_composio._get_composio_api_key``."""
    from skills.skill_composio import _get_composio_api_key

    return _get_composio_api_key()


def _get_composio_client(*, with_crewai_provider: bool = False):
    """Initialise le client Composio (lazy)."""
    api_key = _resolve_api_key()
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
