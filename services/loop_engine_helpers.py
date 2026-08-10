"""Loop Engine helpers — iteration caps and strict-surface detection."""

from __future__ import annotations

from typing import Any


def default_max_iterations() -> int:
    try:
        from config.settings import get_settings

        return int(getattr(get_settings(), "loop_max_iterations", 3))
    except Exception:
        return 3


def strict_max_iterations() -> int:
    try:
        from config.settings import get_settings

        return int(getattr(get_settings(), "loop_strict_max_iterations", 2))
    except Exception:
        return 2


# Merge / ship / deploy / integrator — ceiling = LOOP_STRICT_MAX_ITERATIONS.
_STRICT_TOKENS = frozenset(
    {
        "merge",
        "auto_merge",
        "deploy",
        "release",
        "ship",
        "integrate",
        "hotfix",
        "rollback",
    }
)
_STRICT_AGENTS = frozenset({"dev_integrator", "fix_pipeline"})


def is_strict_loop(
    *,
    agent_id: str = "",
    method: str = "",
    recipe_id: str = "",
    step_id: str = "",
    kwargs: dict[str, Any] | None = None,
) -> bool:
    """True when the surface is merge/destructive (strict iteration cap)."""
    aid = (agent_id or "").strip().lower().replace("_agent", "")
    if aid in _STRICT_AGENTS:
        return True
    rid = (recipe_id or "").strip().lower()
    if rid.startswith("ship_") or rid in {"fix_pipeline", "hotfix"}:
        return True
    blob = f"{method} {step_id} {rid}".lower()
    if any(tok in blob for tok in _STRICT_TOKENS):
        return True
    kw = kwargs or {}
    for key in ("auto_merge", "merge", "deploy", "destructive"):
        if kw.get(key) in (True, 1, "1", "true", "yes"):
            return True
    return False


def resolve_max_iterations(
    *,
    strict: bool = False,
    override: int | None = None,
) -> int:
    """Pick loop cap. Strict surfaces are ceiling'd by LOOP_STRICT_MAX_ITERATIONS."""
    base = strict_max_iterations() if strict else default_max_iterations()
    if override is None:
        return max(1, int(base))
    ov = max(1, int(override))
    return min(ov, int(base)) if strict else ov


def retry_sleep_s() -> float:
    try:
        from config.settings import get_settings

        return float(getattr(get_settings(), "loop_retry_sleep_s", 0.0))
    except Exception:
        return 0.0
