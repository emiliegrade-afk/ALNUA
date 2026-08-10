"""PermissionGuard — fail-closed capability checks (DEC-026 / SPEC_CAPABILITY_GUARD)."""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)


class PermissionDeniedError(PermissionError):
    """Raised when an agent lacks a required capability."""


def guard_enabled() -> bool:
    try:
        from config.settings import get_settings

        return bool(getattr(get_settings(), "permission_guard_enabled", True))
    except Exception:
        return True


def check_capability(
    agent_id: str,
    capability: str,
    *,
    resource: str | None = None,
    meta: dict[str, Any] | None = None,
    log: bool = True,
) -> dict[str, Any]:
    """Return decision dict. Never performs the side-effect."""
    from config.capability_catalog import known_capability
    from config.capability_packs import agent_has_capability, normalize_agent_id, pack_for

    aid = normalize_agent_id(agent_id)
    cap = (capability or "").strip()
    enabled = guard_enabled()

    if not enabled:
        decision = {
            "allowed": True,
            "reason": "guard_disabled",
            "agent_id": aid,
            "capability": cap,
            "resource": resource,
            "pack_size": len(pack_for(aid)),
        }
    elif not known_capability(cap):
        decision = {
            "allowed": False,
            "reason": "unknown_capability",
            "agent_id": aid,
            "capability": cap,
            "resource": resource,
            "pack_size": len(pack_for(aid)),
        }
    elif agent_has_capability(aid, cap):
        decision = {
            "allowed": True,
            "reason": "pack_allow",
            "agent_id": aid,
            "capability": cap,
            "resource": resource,
            "pack_size": len(pack_for(aid)),
        }
    else:
        decision = {
            "allowed": False,
            "reason": "pack_deny",
            "agent_id": aid,
            "capability": cap,
            "resource": resource,
            "pack_size": len(pack_for(aid)),
        }

    if log:
        try:
            from services.trust_graph import record_decision

            record_decision(
                agent_id=aid,
                capability=cap,
                allowed=bool(decision["allowed"]),
                reason=str(decision["reason"]),
                resource=resource,
                meta=meta,
            )
        except Exception:
            pass

    if not decision["allowed"]:
        logger.warning(
            "permission_guard DENY agent=%s cap=%s reason=%s resource=%s",
            aid,
            cap,
            decision["reason"],
            resource,
        )
    return decision


def require_capability(
    agent_id: str,
    capability: str,
    *,
    resource: str | None = None,
    meta: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Allow or raise PermissionDeniedError (no side-effect on deny)."""
    decision = check_capability(
        agent_id,
        capability,
        resource=resource,
        meta=meta,
        log=True,
    )
    if not decision.get("allowed"):
        raise PermissionDeniedError(
            f"Capability denied: agent={agent_id!r} capability={capability!r} "
            f"reason={decision.get('reason')}"
        )
    return decision


def merge_capability_for_branch(target_branch: str) -> str | None:
    """Map protected branch → required capability (None = no merge cap)."""
    branch = (target_branch or "").strip().lower()
    if branch in {"main", "master"}:
        return "git:merge:main"
    if branch == "staging":
        return "git:merge:staging"
    return None


__all__ = [
    "PermissionDeniedError",
    "check_capability",
    "guard_enabled",
    "merge_capability_for_branch",
    "require_capability",
]
