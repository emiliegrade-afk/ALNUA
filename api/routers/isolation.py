"""Agent isolation status API — Phase A (DEC-022)."""

from __future__ import annotations

from typing import Any

from api.route_common import *  # noqa: F403
from pydantic import BaseModel, Field

router = APIRouter(tags=["isolation"])


class ForceReleaseBody(BaseModel):
    key: str = Field(..., min_length=3, max_length=512)
    reason: str = Field(default="admin", max_length=200)


@router.get("/isolation/locks")
def isolation_locks() -> dict[str, Any]:
    from services.resource_locks import list_locks, purge_expired

    purged = purge_expired()
    return {"locks": list_locks(), "purged_expired": purged}


@router.get("/isolation/slots")
def isolation_slots() -> dict[str, Any]:
    from services.execution_slots import slot_status

    return slot_status()


@router.get("/isolation/status")
def isolation_status() -> dict[str, Any]:
    from services.agent_isolation import isolation_enabled
    from services.execution_slots import slot_status
    from services.loop_engine import default_max_iterations, strict_max_iterations
    from services.merge_policy import PROTECTED_BRANCHES
    from services.resource_locks import list_locks, purge_expired

    purged = purge_expired()
    try:
        from config.settings import get_settings

        s = get_settings()
        settings = {
            "enabled": isolation_enabled(),
            "max_global": s.isolation_max_global,
            "max_per_repo": s.isolation_max_per_repo,
            "max_per_agent": s.isolation_max_per_agent,
            "lock_ttl_s": s.isolation_lock_ttl_s,
            "wait_s": s.isolation_wait_s,
            "integrator_only_merge": s.isolation_integrator_only_merge,
            "fix_pipeline_merge": s.isolation_fix_pipeline_merge,
            "loop_max_iterations": s.loop_max_iterations,
            "loop_strict_max_iterations": s.loop_strict_max_iterations,
            "loop_retry_sleep_s": s.loop_retry_sleep_s,
        }
    except Exception:
        settings = {
            "enabled": isolation_enabled(),
            "loop_max_iterations": default_max_iterations(),
            "loop_strict_max_iterations": strict_max_iterations(),
        }

    return {
        "settings": settings,
        "protected_branches": sorted(PROTECTED_BRANCHES),
        "locks": list_locks(),
        "slots": slot_status(),
        "purged_expired": purged,
    }


@router.get("/loop/defaults")
def loop_defaults() -> dict[str, Any]:
    """Loop Engine caps (DEC-024)."""
    from services.loop_engine import default_max_iterations, strict_max_iterations

    strict_applies_to = [
        "merge",
        "deploy",
        "ship_* recipes",
        "dev_integrator",
        "fix_pipeline",
    ]
    try:
        from config.settings import get_settings

        s = get_settings()
        return {
            "max_iterations": s.loop_max_iterations,
            "strict_max_iterations": s.loop_strict_max_iterations,
            "retry_sleep_s": s.loop_retry_sleep_s,
            "strict_applies_to": strict_applies_to,
        }
    except Exception:
        return {
            "max_iterations": default_max_iterations(),
            "strict_max_iterations": strict_max_iterations(),
            "retry_sleep_s": 0.0,
            "strict_applies_to": strict_applies_to,
        }


@router.post("/isolation/locks/release")
def isolation_force_release(body: ForceReleaseBody) -> dict[str, Any]:
    from services.input_sanitizer import sanitize_user_input
    from services.resource_locks import force_release

    key = sanitize_user_input(body.key, redact_pii_enabled=False)[:512]
    reason = sanitize_user_input(body.reason, redact_pii_enabled=False)[:200]
    ok = force_release(key, reason=reason)
    return {"released": ok, "key": key}
