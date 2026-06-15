"""Health + lightweight status (no DB)."""

from __future__ import annotations

import time

from api.route_common import *  # noqa: F403

router = APIRouter()

_HUB_STARTED_AT = time.monotonic()


@router.get("/health")
def health() -> dict[str, str]:
    """Public ping — no API key."""
    return {"status": "ok", "service": "alnua-hub"}


@router.get("/status")
def hub_status() -> dict[str, object]:
    """Fast authenticated ping (X-Hub-Key required) — use for UI health checks."""
    return {
        "status": "ok",
        "service": "alnua-hub",
        "uptime_s": round(time.monotonic() - _HUB_STARTED_AT, 1),
    }
