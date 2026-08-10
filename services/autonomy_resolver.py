"""Trust → autonomy_level resolver (DEC-011 / Phase 30).

Maps agent trust score (0–1) to workflow/idle autonomy_level (0–3):

- score < 0.70  → 0 — manager validation required; no auto-OK post-load steps
- 0.70 ≤ score < 0.80 → 1 — Review Board band; 1 post-load step may auto-OK
- 0.80 ≤ score < 0.90 → 2 — mid-high trust; 2 post-load steps may auto-OK
- score ≥ 0.90  → 3 — low-risk validation workflows may run fully autonomous

``IDLE_DEFAULT_AUTONOMY_LEVEL`` (settings) is the fallback when ``agent_id`` is
empty and an optional floor for idle scheduler jobs (never raises level 0 agents
above 0 — low trust stays gated).
"""

from __future__ import annotations

from typing import Any

from services.idle_work_queue import clamp_autonomy, max_idle_level_for_autonomy


def _settings_idle_default() -> int:
    try:
        from config.settings import settings

        return clamp_autonomy(getattr(settings, "idle_default_autonomy_level", 1))
    except Exception:
        return 1


def trust_score_to_autonomy(score: float) -> int:
    """Pure trust-band mapping (no settings)."""
    s = float(score)
    if s < 0.70:
        return 0
    if s < 0.80:
        return 1
    if s < 0.90:
        return 2
    return 3


def resolve_autonomy_level(agent_id: str, *, default: int | None = None) -> int:
    """Resolve autonomy_level 0–3 from agent trust, with optional default fallback."""
    aid = (agent_id or "").strip()
    fallback = _settings_idle_default() if default is None else clamp_autonomy(default)

    if not aid:
        return fallback

    try:
        from services.agent_trust import get_trust

        row: dict[str, Any] = get_trust(aid)
        score = float(row.get("score") or 0.0)
    except Exception:
        return fallback

    return trust_score_to_autonomy(score)


def resolve_idle_autonomy_level(agent_id: str = "coo", *, apply_settings_floor: bool = True) -> int:
    """Trust-driven autonomy for idle plan/drain, with optional settings floor."""
    level = resolve_autonomy_level(agent_id)
    if not apply_settings_floor:
        return level
    floor = _settings_idle_default()
    if level == 0:
        return 0
    return max(level, floor)


def resolve_idle_max_level(autonomy_level: int) -> int:
    """Map autonomy_level 0–3 → max idle L0–L2 (0→L0, 1→L1, 2/3→L2)."""
    return max_idle_level_for_autonomy(autonomy_level)
