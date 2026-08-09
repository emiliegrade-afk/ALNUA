"""Hub CRUD — peeled from core.py (debt paydown)."""

from __future__ import annotations

from api.route_common import *  # noqa: F403

router = APIRouter()

@router.get("/projects")
def list_projects(branch: str | None = None) -> list[dict[str, Any]]:
    db = get_supabase()
    filters = {"branch": branch} if branch else None
    return db.select("projects", filters=filters, order_by="name")


@router.get("/projects/{project_id}")
def get_project(project_id: str) -> dict[str, Any]:
    db = get_supabase()
    rows = db.select("projects", filters={"id": project_id})
    if not rows:
        raise HTTPException(status_code=404, detail="Project not found")
    return rows[0]


@router.post("/projects")
def create_project(body: ProjectCreate) -> dict[str, Any]:
    """Crée un projet ALNUA et son dossier brainstorm_notes/[slug]."""
    db = get_supabase()
    try:
        row = db.insert(
            "projects",
            {
                "name": body.name.strip(),
                "branch": body.branch,
                "description": body.description.strip(),
                "status": body.status,
            },
        )
        BrainstormAgent.ensure_project_notes_dir(row["name"], row["id"])
        return row
    except Exception as exc:
        msg = str(exc)
        if "row-level security" in msg.lower() or "42501" in msg:
            raise HTTPException(
                status_code=503,
                detail=(
                    "Supabase RLS bloque la création. Utilise la clé service_role "
                    "ou exécute database/fix_rls_dev.sql."
                ),
            ) from exc
        logger.exception("create_project failed")
        raise HTTPException(status_code=500, detail=msg) from exc


@router.delete("/projects/{project_id}")
def delete_project(project_id: str) -> dict[str, str]:
    """Supprime un projet et ses données liées (cascade Supabase)."""
    db = get_supabase()
    rows = db.select("projects", filters={"id": project_id}, limit=1)
    if not rows:
        raise HTTPException(status_code=404, detail="Project not found")
    try:
        db.delete("projects", project_id)
        return {"ok": "Projet supprimé"}
    except Exception as exc:
        msg = str(exc)
        if "row-level security" in msg.lower() or "42501" in msg:
            raise HTTPException(
                status_code=503,
                detail=(
                    "Supabase RLS bloque la suppression. Utilise la clé service_role "
                    "ou exécute database/fix_rls_dev.sql."
                ),
            ) from exc
        logger.exception("delete_project failed")
        raise HTTPException(status_code=500, detail=msg) from exc


@router.post("/dev-log")
def create_dev_log(body: DevLogCreate) -> dict[str, Any]:
    db = get_supabase()
    row = db.insert(
        "dev_log",
        {
            "project_id": body.project_id,
            "content": body.content,
            "date": (body.log_date or date.today()).isoformat(),
        },
    )
    return row


@router.get("/dev-log")
def list_dev_log(project_id: str, unused_only: bool = False) -> list[dict[str, Any]]:
    db = get_supabase()
    filters: dict[str, Any] = {"project_id": project_id}
    if unused_only:
        filters["used_for_content"] = False
    return db.select("dev_log", filters=filters, order_by="date", ascending=False)



@router.get("/modules")
def list_modules(project_id: str | None = None) -> list[dict[str, Any]]:
    db = get_supabase()
    filters: dict[str, Any] = {}
    if project_id:
        filters["project_id"] = project_id
    return db.select("project_modules", filters=filters or None, order_by="position", ascending=True)


@router.post("/modules")
def create_module(body: ModuleCreate) -> dict[str, Any]:
    db = get_supabase()
    existing = db.select("project_modules", filters={"project_id": body.project_id})
    return db.insert(
        "project_modules",
        {
            "project_id": body.project_id,
            "name": body.name,
            "status": body.status,
            "progress": body.progress,
            "features_done": body.features_done,
            "features_total": body.features_total,
            "tests_passed_pct": body.tests_passed_pct,
            "open_bugs": body.open_bugs,
            "position": len(existing),
        },
    )


@router.patch("/modules/{module_id}")
def update_module(module_id: str, body: ModuleUpdate) -> dict[str, Any]:
    db = get_supabase()
    rows = db.select("project_modules", filters={"id": module_id})
    if not rows:
        raise HTTPException(status_code=404, detail="Module not found")

    values = body.model_dump(exclude_none=True)
    if not values:
        raise HTTPException(status_code=400, detail="Aucun champ à mettre à jour")
    return db.update("project_modules", module_id, values)


@router.delete("/modules/{module_id}")
def delete_module(module_id: str) -> dict[str, str]:
    db = get_supabase()
    rows = db.select("project_modules", filters={"id": module_id})
    if not rows:
        raise HTTPException(status_code=404, detail="Module not found")
    db.delete("project_modules", module_id)
    return {"status": "deleted"}


