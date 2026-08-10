"""Brainstorm session routes (legacy mount under releases router)."""

from __future__ import annotations

from api.route_common import *  # noqa: F403
from api.routers.releases_helpers import clean_release_text

router = APIRouter()


@router.post("/agents/brainstorm")
def brainstorm(body: BrainstormRequest) -> dict[str, Any]:
    agent = BrainstormAgent()
    return agent.brainstorm(
        body.project_id, clean_release_text(body.topic, max_length=500), clean_release_text(body.context_notes)
    )


@router.post("/agents/brainstorm/chat")
def brainstorm_chat(body: BrainstormChatRequest) -> dict[str, Any]:
    settings = get_settings()
    if not settings.openrouter_api_key.strip():
        raise HTTPException(
            status_code=503,
            detail="OPENROUTER_API_KEY manquante — ajoute-la dans c:\\Dev\\ALUNA_HUB\\.env",
        )
    if not settings.supabase_url.strip() or not settings.supabase_key.strip():
        raise HTTPException(
            status_code=503,
            detail="SUPABASE_URL / SUPABASE_KEY manquantes dans .env",
        )
    try:
        agent = BrainstormAgent()
        return agent.chat(clean_release_text(body.message), body.project_id, body.session_id)
    except Exception as exc:
        msg = str(exc)
        if "row-level security" in msg.lower() or "42501" in msg:
            raise HTTPException(
                status_code=503,
                detail=(
                    "Supabase RLS bloque l'écriture. Utilise la clé service_role dans "
                    "SUPABASE_KEY, ou exécute database/fix_rls_dev.sql dans Supabase."
                ),
            ) from exc
        logger.exception("brainstorm_chat failed")
        raise HTTPException(status_code=500, detail=msg) from exc


@router.get("/brainstorm/sessions")
def brainstorm_sessions(limit: int = Query(default=30, le=100)) -> list[dict[str, Any]]:
    agent = BrainstormAgent()
    sessions = agent.list_sessions(limit=limit)
    sessions = agent.attach_summaries_to_sessions(sessions)
    db = get_supabase()
    projects = {p["id"]: p["name"] for p in db.select("projects")}
    for session in sessions:
        pid = session.get("project_id")
        session["project_name"] = projects.get(pid, "ALNUA Global") if pid else "ALNUA Global"
    return sessions


@router.post("/brainstorm/sessions/{session_id}/summarize")
def brainstorm_summarize(session_id: str) -> dict[str, Any]:
    """Génère une fiche markdown, l'exporte et la sauvegarde en base."""
    settings = get_settings()
    if not settings.openrouter_api_key.strip():
        raise HTTPException(status_code=503, detail="OPENROUTER_API_KEY manquante")
    agent = BrainstormAgent()
    try:
        agent.get_session(session_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    try:
        return agent.summarize_session(session_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        logger.exception("brainstorm_summarize failed")
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.get("/brainstorm/sessions/{session_id}/summary")
def brainstorm_session_summary(session_id: str) -> dict[str, Any]:
    """Retourne le compte-rendu existant d'une session."""
    agent = BrainstormAgent()
    summary = agent.get_summary_for_session(session_id)
    if not summary:
        raise HTTPException(status_code=404, detail="Aucun compte-rendu pour cette session")
    return summary


@router.post("/brainstorm/summaries/reveal")
def reveal_summary_file(body: RevealFileRequest) -> dict[str, bool]:
    """Ouvre le fichier .md dans l'explorateur Windows (API locale)."""
    path = Path(body.file_path).resolve()
    root = BRAINSTORM_NOTES_ROOT.resolve()
    try:
        path.relative_to(root)
    except ValueError as exc:
        raise HTTPException(status_code=403, detail="Chemin non autorisé") from exc
    if not path.is_file():
        raise HTTPException(status_code=404, detail="Fichier introuvable")
    subprocess.Popen(["explorer", "/select,", str(path)])
    return {"ok": True}


@router.get("/brainstorm/sessions/{session_id}")
def brainstorm_session(session_id: str) -> dict[str, Any]:
    agent = BrainstormAgent()
    try:
        return agent.get_session(session_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/brainstorm/welcome")
def brainstorm_welcome() -> dict[str, str]:
    return {"message": WELCOME_MESSAGE}
