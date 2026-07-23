"""Hub web IDE — workspaces, files, sandbox terminal, live agent worktree."""

from __future__ import annotations

from api.route_common import *  # noqa: F403

router = APIRouter()


class IdeFileWriteBody(BaseModel):
    workspace: str = "hub"
    path: str
    content: str


class IdeRunBody(BaseModel):
    command: str
    cwd: str = "."


class CodingCoachAskBody(BaseModel):
    message: str
    workspace: str = "sandbox"
    file_path: str | None = None
    file_content: str | None = None


@router.get("/ide/workspaces")
def ide_list_workspaces() -> dict[str, Any]:
    from services.ide_workspace import list_workspaces

    return {
        "workspaces": [
            {
                "id": w.id,
                "label": w.label,
                "path": w.path,
                "kind": w.kind,
                "readOnly": w.read_only,
                "active": w.active,
            }
            for w in list_workspaces()
        ]
    }


@router.get("/ide/tree")
def ide_tree(workspace: str = "hub", path: str = ".") -> dict[str, Any]:
    from services.ide_workspace import list_tree

    try:
        return list_tree(workspace, path)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/ide/file")
def ide_read_file(workspace: str = "hub", path: str = "") -> dict[str, Any]:
    from services.ide_workspace import read_file

    if not path:
        raise HTTPException(status_code=400, detail="path requis")
    try:
        return read_file(workspace, path)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.put("/ide/file")
def ide_write_file(body: IdeFileWriteBody) -> dict[str, str]:
    from services.ide_workspace import write_file

    try:
        return write_file(body.workspace, body.path, body.content)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/ide/diff")
def ide_diff(workspace: str = "hub") -> dict[str, str]:
    from services.ide_workspace import git_diff

    try:
        return {"workspace": workspace, "diff": git_diff(workspace)}
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/ide/run")
def ide_run_sandbox(body: IdeRunBody) -> dict[str, Any]:
    from services.ide_workspace import run_sandbox_command

    try:
        return run_sandbox_command(body.command, cwd_rel=body.cwd)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/ide/live")
def ide_live_status() -> dict[str, Any]:
    """Agent coding activity for IDE sidebar."""
    from services.coding_activity import active_tasks, recent_tasks

    active = active_tasks()
    return {
        "active": active,
        "recent": recent_tasks(limit=5),
        "hasAgentWork": len(active) > 0,
    }


@router.get("/ide/hermes-skills")
def ide_hermes_skills() -> dict[str, Any]:
    from services.hermes_skills import list_catalog

    return list_catalog()


@router.get("/ide/hermes-skills/{skill_id:path}")
def ide_hermes_skill_detail(skill_id: str) -> dict[str, Any]:
    from services.hermes_skills import load_skill_body, load_skill_meta

    meta = load_skill_meta(skill_id)
    if not meta:
        raise HTTPException(status_code=404, detail="Skill introuvable")
    return {**meta, "body": load_skill_body(skill_id) or ""}


@router.post("/ide/coach/ask")
def ide_coach_ask(body: CodingCoachAskBody) -> dict[str, str]:
    from agents.coding_coach_agent import CodingCoachAgent

    agent = CodingCoachAgent()
    reply = agent.teach(
        body.message,
        workspace=body.workspace,
        file_path=body.file_path,
        file_content=body.file_content,
    )
    return {"reply": reply, "agent": "coding_coach"}
