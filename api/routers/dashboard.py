"""Auto-split from api/main.py — dashboard routes."""

from __future__ import annotations

from api.route_common import *  # noqa: F403

router = APIRouter()


@router.websocket("/ws/coo")
async def websocket_coo(websocket: WebSocket):
    if not await accept_authenticated_websocket(websocket):
        return
    try:
        while True:
            data = await websocket.receive_json()
            await websocket.send_json({"type": "thinking", "message": "Analyse en cours…"})
            response = await asyncio.to_thread(
                get_coo_agent().handle_instruction,
                data.get("message", ""),
            )
            await websocket.send_json({"type": "response", "message": response})
            await websocket.send_json({"type": "speaking", "message": response[:120]})
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)


@router.websocket("/ws/pipeline")
async def websocket_pipeline(websocket: WebSocket):
    if not await accept_authenticated_websocket(websocket):
        return
    try:
        while True:
            await asyncio.sleep(5)
            await websocket.send_json(
                {"type": "heartbeat", "message": "Pipeline actif — polling GitHub"}
            )
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)


@router.get("/brief/today")
async def get_brief_today():
    """Brief matinal formaté pour le dashboard."""
    try:
        briefing = await asyncio.to_thread(get_coo_agent().get_daily_briefing)
    except Exception as exc:
        logger.exception("brief/today failed")
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    projects = []
    urgent: list[str] = []
    for ctx in briefing.get("projects", []):
        project = ctx.get("project", {})
        projects.append(
            {
                "name": project.get("name", "?"),
                "branch": project.get("branch", "app"),
                "status": project.get("status", "active"),
            }
        )
        for ticket in ctx.get("critical_tickets", []):
            urgent.append(f"[{project.get('name', '?')}] {ticket.get('title', '')}")

    return {
        "date": briefing.get("date"),
        "projects": projects,
        "urgent": urgent,
        "summary": briefing.get("summary"),
    }


@router.get("/github/prs")
async def get_github_prs():
    try:
        return get_open_prs()
    except ValueError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.get("/branches/app")
async def get_app_branch():
    db = get_supabase()
    rows = db.select("projects", filters={"branch": "app"}, order_by="name")
    projects = [
        {
            "name": p["name"],
            "status": p.get("status", "active"),
            "progress": _branch_progress(p.get("status", "")),
        }
        for p in rows
    ]
    return {"projects": projects, "agents": ["DevApp", "UX"]}


@router.get("/branches/gaming")
async def get_gaming_branch():
    db = get_supabase()
    rows = db.select("projects", filters={"branch": "gaming"}, order_by="name")
    projects = [
        {
            "name": p["name"],
            "status": p.get("status", "active"),
            "progress": _branch_progress(p.get("status", "")),
        }
        for p in rows
    ]
    return {"projects": projects, "agents": ["GameDirector", "DevGaming", "ArtDirector"]}


@router.get("/branches/robo")
async def get_robo_branch():
    db = get_supabase()
    rows = db.select("projects", filters={"branch": "robotics"}, order_by="name")
    projects = [
        {
            "name": p["name"],
            "status": p.get("status", "active"),
            "progress": _branch_progress(p.get("status", "")),
        }
        for p in rows
    ]
    return {"projects": projects, "agents": ["Hardware", "EmbeddedDev"]}


def _branch_progress(status: str) -> int:
    mapping = {
        "live": 100,
        "deployed": 100,
        "mvp": 85,
        "active": 60,
        "in_progress": 40,
        "rd": 15,
        "research": 10,
        "planned": 5,
    }
    return mapping.get((status or "").lower().replace(" ", "_"), 25)


@router.get("/eve/status")
async def get_eve_status():
    from skills.skill_pi_ssh import pi_ssh_command_raw

    try:
        status = pi_ssh_command_raw("python3 /home/pi/eve/status.py")
        battery = 75
        if "battery" in status.lower():
            import re

            match = re.search(r"(\d{1,3})\s*%", status)
            if match:
                battery = int(match.group(1))
        return {"connected": True, "battery": battery, "raw": status}
    except Exception:
        return {"connected": False, "battery": None}


