"""Nadia desktop companion — PC boot + Hub bridge."""

from __future__ import annotations

from api.route_common import *  # noqa: F403

router = APIRouter(prefix="/nadia/desktop", tags=["nadia"])


@router.get("/status")
def nadia_desktop_status() -> dict:
    from services.nadia_desktop import desktop_status

    return desktop_status()


@router.post("/boot")
def nadia_desktop_boot(source: str = "desktop") -> dict:
    """Register PC session start — call from logon script or UI."""
    from services.nadia_desktop import register_pc_boot

    return register_pc_boot(source=source)
