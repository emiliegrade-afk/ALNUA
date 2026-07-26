"""Auto-split from api/main.py — releases routes."""

from __future__ import annotations

from api.route_common import *  # noqa: F403
from services.input_sanitizer import sanitize_user_input

router = APIRouter()


def _clean(text: str, *, max_length: int = 6000) -> str:
    return sanitize_user_input(text, max_length=max_length)


def _enrich_releases_with_project_names(
    db: Any, releases: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    if not releases:
        return releases
    project_ids = {r["project_id"] for r in releases if r.get("project_id")}
    names: dict[str, str] = {}
    for pid in project_ids:
        rows = db.select("projects", filters={"id": pid}, columns="id,name")
        if rows:
            names[pid] = rows[0]["name"]
    for release in releases:
        pid = release.get("project_id")
        if pid and pid in names:
            release["project_name"] = names[pid]
    return releases


@router.get("/releases")
def list_releases(project_id: str | None = None) -> list[dict[str, Any]]:
    db = get_supabase()
    try:
        query = db.table("releases").select("*").order("created_at", desc=True)
        if project_id:
            query = query.eq("project_id", project_id)
        response = query.execute()
        return _enrich_releases_with_project_names(db, response.data or [])
    except Exception as exc:
        msg = str(exc)
        if "releases" in msg and ("PGRST205" in msg or "schema cache" in msg):
            logger.warning("releases table missing — returning empty list")
            return []
        logger.exception("list_releases failed")
        raise HTTPException(status_code=500, detail="Impossible de charger les releases") from exc


@router.post("/releases/generate")
def generate_release(body: ReleaseGenerateRequest) -> dict[str, Any]:
    result = generate_release_notes(
        project_id=body.project_id,
        version=body.version.strip(),
        since_date=body.since_date,
        dev_log_ids=body.dev_log_ids,
    )
    db = get_supabase()
    enriched = _enrich_releases_with_project_names(db, [result["release"]])
    return enriched[0]


@router.get("/releases/generate")
def get_release_generate_not_allowed() -> None:
    """Static path before {release_id} — avoid treating 'generate' as a UUID."""
    raise HTTPException(
        status_code=405,
        detail="Utiliser POST /releases/generate",
    )


@router.get("/releases/{release_id}")
def get_release(release_id: str) -> dict[str, Any]:
    db = get_supabase()
    rows = db.select("releases", filters={"id": release_id})
    if not rows:
        raise HTTPException(status_code=404, detail="Release introuvable")
    enriched = _enrich_releases_with_project_names(db, rows)
    return enriched[0]


@router.patch("/releases/{release_id}")
def update_release(release_id: str, body: ReleaseUpdate) -> dict[str, Any]:
    db = get_supabase()
    existing = db.select("releases", filters={"id": release_id})
    if not existing:
        raise HTTPException(status_code=404, detail="Release introuvable")

    updates = body.model_dump(exclude_none=True)
    if not updates:
        raise HTTPException(status_code=400, detail="Aucune modification fournie")
    if "release_date" in updates and updates["release_date"] is not None:
        updates["release_date"] = updates["release_date"].isoformat()

    row = db.update("releases", release_id, updates)
    enriched = _enrich_releases_with_project_names(db, [row])
    return enriched[0]


@router.delete("/releases/{release_id}")
def delete_release(release_id: str) -> dict[str, bool]:
    db = get_supabase()
    existing = db.select("releases", filters={"id": release_id})
    if not existing:
        raise HTTPException(status_code=404, detail="Release introuvable")
    db.delete("releases", release_id)
    return {"ok": True}


@router.post("/agents/coo/briefing")
def coo_briefing() -> dict[str, str]:
    agent = COOAgent()
    briefing = agent.run_daily_briefing()
    return {"briefing": briefing}


@router.post("/agents/coo/instruction", response_model=COOInstructionResponse)
def coo_instruction(body: COOInstruction) -> COOInstructionResponse:
    try:
        result = get_coo_agent().process_message(body.instruction, body.project)
        return COOInstructionResponse(**result)
    except Exception as exc:
        logger.exception("COO instruction failed: %s", exc)
        return COOInstructionResponse(
            response=f"Erreur COO : {exc}",
            issue_created=False,
        )


@router.post("/webhook/telegram")
async def telegram_webhook(request: Request) -> dict[str, bool]:
    """Receives Telegram updates (webhook mode — production)."""
    import secrets

    settings = get_settings()
    if not settings.telegram_bot_token:
        raise HTTPException(status_code=503, detail="Telegram bot not configured")

    webhook_secret = settings.telegram_webhook_secret.strip()
    env = settings.environment.strip().lower()
    is_prod = env in {"production", "prod", "staging"}
    if webhook_secret:
        provided = request.headers.get("X-Telegram-Bot-Api-Secret-Token", "")
        if not provided or not secrets.compare_digest(provided, webhook_secret):
            raise HTTPException(status_code=401, detail="Telegram webhook secret invalide")
    elif is_prod:
        raise HTTPException(
            status_code=503,
            detail="TELEGRAM_WEBHOOK_SECRET requis en production",
        )

    update_data = await request.json()
    await get_telegram_bot().process_update(update_data)
    return {"ok": True}


@router.post("/webhook/telegram/secretary")
async def telegram_secretary_webhook(request: Request) -> dict[str, bool]:
    """Webhook Telegram — bot Nadia (secrétaire)."""
    import secrets

    settings = get_settings()
    if not settings.telegram_secretary_bot_token:
        raise HTTPException(status_code=503, detail="Telegram secretary bot not configured")

    webhook_secret = settings.telegram_secretary_webhook_secret.strip()
    env = settings.environment.strip().lower()
    is_prod = env in {"production", "prod", "staging"}
    if webhook_secret:
        provided = request.headers.get("X-Telegram-Bot-Api-Secret-Token", "")
        if not provided or not secrets.compare_digest(provided, webhook_secret):
            raise HTTPException(status_code=401, detail="Telegram secretary webhook secret invalide")
    elif is_prod:
        raise HTTPException(
            status_code=503,
            detail="TELEGRAM_SECRETARY_WEBHOOK_SECRET requis en production",
        )

    from bots.telegram_secretary_bot import get_telegram_secretary_bot

    update_data = await request.json()
    await get_telegram_secretary_bot().process_update(update_data)
    return {"ok": True}


@router.post("/agents/pm/triage/{project_id}")
def pm_triage(project_id: str) -> dict[str, Any]:
    agent = PMAgent()
    return agent.triage_project(project_id)


@router.post("/agents/qa/analyze/{project_id}")
def qa_analyze(project_id: str) -> dict[str, Any]:
    agent = QAAgent()
    return agent.analyze_feedback_batch(project_id)


_SECTOR_AGENT_CLASSES: dict[str, tuple[str, str]] = {
    "app": ("agents.content_app_agent", "ContentAppAgent"),
    "gaming": ("agents.content_gaming_agent", "ContentGamingAgent"),
    "robo": ("agents.content_robo_agent", "ContentRoboAgent"),
    "company": ("agents.content_company_agent", "ContentCompanyAgent"),
}


def _resolve_content_agent(sector: str | None) -> ContentAgent:
    if not sector:
        return ContentAgent()
    import importlib

    module_path, class_name = _SECTOR_AGENT_CLASSES[sector]
    module = importlib.import_module(module_path)
    agent_class = getattr(module, class_name)
    return agent_class()


@router.post("/agents/content/generate")
def content_generate(body: ContentGenerateRequest) -> dict[str, Any]:
    agent = _resolve_content_agent(body.sector)
    try:
        posts = agent.generate_posts(
            body.project_id,
            body.dev_log,
            body.content_types,
            body.platforms,
            alnua_global=body.alnua_global,
        )
        return {"posts_created": len(posts), "posts": posts}
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        logger.exception("content_generate failed")
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.post("/agents/content/generate/{project_id}")
def content_generate_legacy(project_id: str) -> dict[str, Any]:
    agent = ContentAgent()
    posts = agent.generate_from_dev_logs(project_id)
    return {"posts_created": len(posts), "posts": posts}


@router.post("/agents/brainstorm")
def brainstorm(body: BrainstormRequest) -> dict[str, Any]:
    agent = BrainstormAgent()
    return agent.brainstorm(
        body.project_id, _clean(body.topic, max_length=500), _clean(body.context_notes)
    )


@router.post("/agents/brainstorm/chat")
def brainstorm_chat(body: BrainstormChatRequest) -> dict[str, Any]:
    settings = get_settings()
    if not settings.openrouter_api_key.strip():
        raise HTTPException(
            status_code=503,
            detail="OPENROUTER_API_KEY manquante — ajoute-la dans c:\\Dev\\ALNUA_HUB\\.env",
        )
    if not settings.supabase_url.strip() or not settings.supabase_key.strip():
        raise HTTPException(
            status_code=503,
            detail="SUPABASE_URL / SUPABASE_KEY manquantes dans .env",
        )
    try:
        agent = BrainstormAgent()
        return agent.chat(_clean(body.message), body.project_id, body.session_id)
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


@router.post("/agents/spec/{ticket_id}")
def spec_generate(ticket_id: str) -> dict[str, Any]:
    agent = SpecAgent()
    return agent.generate_cursor_prompt(ticket_id)


@router.get("/agents/logs")
def agent_logs(limit: int = Query(default=50, le=200)) -> list[dict[str, Any]]:
    db = get_supabase()
    return db.select("agent_logs", order_by="created_at", ascending=False, limit=limit)


