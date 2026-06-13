"""Auto-split from api/main.py — scanner routes."""

from __future__ import annotations

from api.route_common import *  # noqa: F403

router = APIRouter()



@router.post("/agents/scan")
async def trigger_project_scan():
    """Déclenche un scan immédiat de tous les projets GitHub + fichiers locaux."""
    import threading
    from agents.project_scanner import scan_all_projects
    threading.Thread(target=scan_all_projects, daemon=True).start()
    return {"status": "scan démarré en arrière-plan"}


@router.get("/agents/errors")
async def get_open_errors():
    """Liste les erreurs ouvertes dans le journal."""
    from skills.skill_error_journal import get_open_errors_summary
    return {"summary": get_open_errors_summary()}


