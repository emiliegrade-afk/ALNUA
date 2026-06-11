"""ALNUA Hub — FastAPI REST API."""

from __future__ import annotations

import asyncio
import csv
import io
import logging
import os
import subprocess
import uuid
import zipfile
from contextlib import asynccontextmanager
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import sentry_sdk
from fastapi import (
    Depends,
    FastAPI,
    File,
    Form,
    Header,
    HTTPException,
    Query,
    Request,
    UploadFile,
    WebSocket,
    WebSocketDisconnect,
)
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, RedirectResponse, StreamingResponse
from pydantic import BaseModel, Field

from agents.brainstorm_agent import BrainstormAgent, BRAINSTORM_NOTES_ROOT, WELCOME_MESSAGE
from agents.content_agent import ContentAgent
from agents.coo_agent import COOAgent
from agents.pm_agent import PMAgent
from agents.qa_agent import QAAgent
from agents.spec_agent import SpecAgent
from api.analytics_helpers import (
    filter_by_date_range,
    latest_values_by_project,
    month_bounds,
    parse_period,
    pct_change,
    previous_month_bounds,
    sum_metric_in_range,
)
from bots.sav_bot import SAVBot
from bots.telegram_bot import get_telegram_bot
from config.settings import get_settings
from database.supabase_client import get_supabase
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

from services.beta_portal import (
    create_feedback_ticket,
    create_tester_token,
    decode_tester_token,
    get_tester_or_404,
    invite_url_for_slug,
    latest_app_version,
    project_slug_for,
    resolve_project_by_slug,
    upload_screenshot,
)
from services.brand_schemas import BrandAnalysis, BrandElement
from services.brand_storage import BRAND_KITS_ROOT, ensure_brand_kit_dirs
from services.briefing_generator import (
    generate_and_store_daily_briefing,
    get_briefing_for_date,
)
from services.kit_generator import ALL_FORMAT_NAMES, generate_full_kit
from services.palette import extract_kmeans_colors, merge_palettes
from services.report_generator import REPORT_FILENAME, generate_brand_report
from services.release_generator import generate_release_notes
from services.segmentation import generate_isolated_assets, segment_elements
from services.vision_llm import analyze_brand_image, prepare_brand_image
from services.partnerships import (
    AFFILIATE_FALLBACK_URL,
    CONTRACTS_ROOT,
    affiliate_link_timeline,
    affiliate_public_url,
    build_contract_path,
    ensure_contract_dirs,
    generate_affiliate_code,
    open_contract_file,
    open_contracts_folder,
    parse_audience_size_text,
    partnership_stats,
    record_affiliate_click,
    record_affiliate_conversion,
    run_partnership_followup_reminders,
)
from services.waitlist import (
    compute_position,
    generate_waitlist_email,
    markdown_to_html,
    waitlist_stats,
    waitlist_url_for_slug,
)
from services.finance_agent import (
    attach_project_names,
    build_dashboard,
    fetch_transactions as fetch_finance_transactions,
    generate_monthly_summary,
    get_or_generate_summary,
)
from skills.skill_gh_issues import (
    get_issue,
    get_open_prs,
    list_ready_issues,
    poll_issues_loop,
    process_issue,
)
from skills.skill_model_usage import get_daily_costs, get_monthly_costs, get_weekly_costs

logger = logging.getLogger(__name__)

_briefing_scheduler: BackgroundScheduler | None = None


def _run_scheduled_daily_briefing() -> None:
    try:
        generate_and_store_daily_briefing(skip_if_exists=True)
        logger.info("Scheduled daily briefing generated")
    except Exception:
        logger.exception("Scheduled daily briefing failed")


def _run_partnership_followup_reminders() -> None:
    try:
        count = run_partnership_followup_reminders()
        logger.info("Partnership follow-up reminders: %s ticket(s) created", count)
    except Exception:
        logger.exception("Partnership follow-up reminder job failed")


@asynccontextmanager
async def lifespan(app: FastAPI):
    global _briefing_scheduler
    settings = get_settings()
    if settings.sentry_dsn:
        sentry_sdk.init(dsn=settings.sentry_dsn, traces_sample_rate=0.1)
        logger.info("Sentry initialized")
    try:
        ensure_brand_kit_dirs()
        logger.info("Brand kit directories ready")
    except Exception:
        logger.exception("Could not initialize brand_kits directories")
    try:
        ensure_contract_dirs()
        logger.info("Partnership contract directories ready")
    except Exception:
        logger.exception("Could not initialize contract directories")

    # === SCHEDULER ===
    _briefing_scheduler = BackgroundScheduler()
    _briefing_scheduler.add_job(
        _run_scheduled_daily_briefing,
        CronTrigger(hour=8, minute=0),
        id="daily_briefing",
        replace_existing=True,
    )
    _briefing_scheduler.add_job(
        _run_partnership_followup_reminders,
        CronTrigger(hour=8, minute=5),
        id="partnership_followups",
        replace_existing=True,
    )
    _briefing_scheduler.start()
    logger.info("Daily briefing scheduler started (08:00)")

    from config.github_repos import pipeline_enabled

    if pipeline_enabled():
        asyncio.create_task(poll_issues_loop())
        logger.info("GitHub Issues polling started (multi-repo, agent-ready)")
    else:
        logger.warning(
            "GitHub Issues polling disabled — GITHUB_TOKEN or repo config missing"
        )

    yield

    if settings.telegram_bot_token:
        try:
            await get_telegram_bot().shutdown()
        except Exception:
            logger.exception("Telegram bot shutdown failed")

    if _briefing_scheduler:
        _briefing_scheduler.shutdown(wait=False)
        _briefing_scheduler = None


app = FastAPI(
    title="ALNUA Hub",
    description="Backend IA pour ALNUA — agents, bots et données centralisées",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:3001",
        "http://127.0.0.1:3001",
        "http://localhost:3002",
        "http://127.0.0.1:3002",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# Pydantic models
# ---------------------------------------------------------------------------
class DevLogCreate(BaseModel):
    project_id: str
    content: str
    log_date: date | None = None


class TicketCreate(BaseModel):
    project_id: str
    type: str = Field(pattern="^(bug|feature|improvement|crash)$")
    priority: str = Field(default="medium", pattern="^(critical|high|medium|low)$")
    title: str
    description: str = ""
    source: str = Field(
        default="emilie",
        pattern="^(qa_agent|sav_bot|reviews_bot|emilie|quick_capture|beta_tester|partnerships_bot)$",
    )


class TicketUpdate(BaseModel):
    status: str | None = Field(
        default=None,
        pattern="^(open|in_progress|done|wont_fix)$",
    )
    title: str | None = None
    description: str | None = None
    priority: str | None = Field(
        default=None,
        pattern="^(critical|high|medium|low)$",
    )
    cursor_prompt: str | None = None


class FeedbackCreate(BaseModel):
    project_id: str
    source: str
    content: str
    author: str | None = None
    rating: int | None = Field(default=None, ge=1, le=5)
    sentiment: str = Field(default="neutral", pattern="^(positive|negative|neutral|mixed)$")


class RoadmapCreate(BaseModel):
    project_id: str
    title: str
    description: str = ""
    status: str = Field(
        default="planned",
        pattern="^(idea|planned|in_progress|done)$",
    )
    priority: str = Field(
        default="medium",
        pattern="^(critical|high|medium|low)$",
    )
    phase: str | None = None
    due_date: date | None = None


class RoadmapUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    status: str | None = Field(
        default=None,
        pattern="^(idea|planned|in_progress|done)$",
    )
    priority: str | None = Field(
        default=None,
        pattern="^(critical|high|medium|low)$",
    )


class ReleaseGenerateRequest(BaseModel):
    project_id: str
    version: str = Field(min_length=1, max_length=32)
    since_date: date | None = None
    dev_log_ids: list[str] | None = None


class ReleaseUpdate(BaseModel):
    app_store_notes: str | None = None
    google_play_notes: str | None = None
    changelog_md: str | None = None
    status: str | None = Field(default=None, pattern="^(draft|published)$")
    release_date: date | None = None


class QuickCaptureRequest(BaseModel):
    type: str = Field(pattern="^(ticket|idea|roadmap|note)$")
    content: str = Field(min_length=1)
    project_id: str
    priority: str | None = Field(
        default="medium",
        pattern="^(critical|high|medium|low)$",
    )
    project_id: str | None = None
    phase: str | None = None
    due_date: date | None = None
    linked_ticket_id: str | None = None


class BrainstormRequest(BaseModel):
    project_id: str
    topic: str
    context_notes: str = ""


class BrainstormChatRequest(BaseModel):
    message: str
    project_id: str | None = None
    session_id: str | None = None


class SAVQuestion(BaseModel):
    project_id: str
    question: str
    author: str | None = None


class FAQCreate(BaseModel):
    project_id: str
    question: str
    answer: str
    tags: list[str] = []


class TransactionCreate(BaseModel):
    project_id: str | None = None
    type: str = Field(pattern="^(income|expense|revenue)$")
    amount: float
    currency: str = "EUR"
    category: str
    description: str | None = None
    transaction_date: date | None = None
    is_recurring: bool = False
    recurrence: str | None = None


class FinanceTransactionCreate(BaseModel):
    tx_date: date = Field(alias="date")
    type: str = Field(pattern="^(income|expense)$")
    amount: float = Field(gt=0)
    currency: str = "EUR"
    category: str
    project_id: str | None = None
    description: str | None = None
    is_recurring: bool = False
    recurrence: str | None = Field(default=None, pattern="^(monthly|annual|one_time)$")

    model_config = {"populate_by_name": True}


class FinanceTransactionUpdate(BaseModel):
    tx_date: date | None = Field(default=None, alias="date")
    type: str | None = Field(default=None, pattern="^(income|expense)$")
    amount: float | None = Field(default=None, gt=0)
    currency: str | None = None
    category: str | None = None
    project_id: str | None = None
    description: str | None = None
    is_recurring: bool | None = None
    recurrence: str | None = Field(default=None, pattern="^(monthly|annual|one_time)$")

    model_config = {"populate_by_name": True}


class FinanceSummaryGenerate(BaseModel):
    month: str = Field(pattern=r"^\d{4}-\d{2}$")


class AnalyticsCreate(BaseModel):
    model_config = {"populate_by_name": True}

    project_id: str
    metric_name: str = Field(
        pattern="^(downloads|active_users|subscriptions|mrr|churn|web_visitors)$"
    )
    value: float
    record_date: date | None = Field(default=None, alias="date")
    source: str = Field(
        default="stripe",
        pattern="^(app_store|google_play|stripe|revenuecat|plausible)$",
    )


class COOInstruction(BaseModel):
    instruction: str
    project: str | None = None


class COOInstructionResponse(BaseModel):
    response: str
    issue_created: bool = False
    issue_number: int | None = None
    issue_url: str | None = None
    repo: str | None = None


class ContentGenerateRequest(BaseModel):
    project_id: str
    dev_log: str
    content_types: list[str] = Field(min_length=1)
    platforms: list[str] = Field(min_length=1)
    alnua_global: bool = False


class PostUpdate(BaseModel):
    status: str | None = None
    text_content: str | None = None
    hashtags: list[str] | None = None
    scheduled_at: str | None = None
    image_prompt: str | None = None
    video_script: str | None = None


class ProjectCreate(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    branch: str = Field(pattern="^(app|gaming|robotics|other)$")
    description: str = ""
    status: str = Field(default="dev", pattern="^(active|beta|dev|paused)$")


class RevealFileRequest(BaseModel):
    file_path: str


class BetaRegisterRequest(BaseModel):
    project_slug: str
    email: str = Field(min_length=3)
    first_name: str = Field(min_length=1)
    device: str | None = None
    os_version: str | None = None
    app_version: str | None = None


class BetaFeedbackRequest(BaseModel):
    project_slug: str
    type: str = Field(pattern="^(bug|suggestion|crash|ux|autre)$")
    title: str = Field(min_length=1)
    description: str = ""
    severity: str | None = Field(
        default=None,
        pattern="^(bloquant|majeur|mineur|cosmétique)$",
    )
    screenshot_base64: str | None = None


class BetaInviteRequest(BaseModel):
    project_id: str


class WaitlistJoinRequest(BaseModel):
    project_slug: str
    email: str = Field(min_length=3)
    first_name: str | None = None
    source: str | None = None
    message: str | None = None


class WaitlistNotifyRequest(BaseModel):
    project_id: str
    subject: str = Field(min_length=1)
    message_md: str = Field(min_length=1)
    status_filter: str | None = Field(
        default=None,
        pattern="^(waiting|notified|converted)$",
    )


class WaitlistStatusUpdate(BaseModel):
    status: str = Field(pattern="^(waiting|notified|converted)$")


class WaitlistGenerateEmailRequest(BaseModel):
    project_id: str


class PartnerCreate(BaseModel):
    type: str
    direction: str = Field(pattern="^(outbound|inbound)$")
    name: str = Field(min_length=1)
    status: str = "prospect"
    company: str | None = None
    email: str | None = None
    instagram_url: str | None = None
    tiktok_url: str | None = None
    youtube_url: str | None = None
    website: str | None = None
    audience_size: int | None = None
    audience_description: str | None = None
    project_ids: list[str] | None = None
    notes: str | None = None
    next_followup: date | None = None
    last_contact_date: date | None = None


class PartnerUpdate(BaseModel):
    type: str | None = None
    direction: str | None = Field(default=None, pattern="^(outbound|inbound)$")
    name: str | None = None
    status: str | None = None
    company: str | None = None
    email: str | None = None
    instagram_url: str | None = None
    tiktok_url: str | None = None
    youtube_url: str | None = None
    website: str | None = None
    audience_size: int | None = None
    audience_description: str | None = None
    project_ids: list[str] | None = None
    notes: str | None = None
    contract_path: str | None = None
    next_followup: date | None = None
    last_contact_date: date | None = None


class PartnerInteractionCreate(BaseModel):
    type: str | None = None
    note: str | None = None
    date: datetime | None = None


class AffiliateLinkCreate(BaseModel):
    partner_id: str
    project_id: str | None = None
    code: str | None = None
    redirect_url: str
    commission_type: str | None = Field(default=None, pattern="^(percent|fixed)$")
    commission_value: float | None = None
    active: bool = True


class AffiliateLinkUpdate(BaseModel):
    redirect_url: str | None = None
    commission_type: str | None = Field(default=None, pattern="^(percent|fixed)$")
    commission_value: float | None = None
    active: bool | None = None
    project_id: str | None = None


class AffiliateConversionBody(BaseModel):
    revenue: float = 0.0


class PartnershipRequestCreate(BaseModel):
    name: str = Field(min_length=1)
    email: str = Field(min_length=3)
    type: str | None = None
    message: str | None = None
    instagram_url: str | None = None
    tiktok_url: str | None = None
    website: str | None = None
    audience_size: str | None = None
    project_interest: str | None = None


class PartnershipRequestUpdate(BaseModel):
    status: str | None = Field(
        default=None,
        pattern="^(new|reviewed|converted|declined)$",
    )


def _beta_tester_auth(authorization: str | None = Header(default=None)) -> dict[str, str]:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Token requis")
    token = authorization.removeprefix("Bearer ").strip()
    return decode_tester_token(token)


# ---------------------------------------------------------------------------
# Health
# ---------------------------------------------------------------------------
@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "alnua-hub"}


# ---------------------------------------------------------------------------
# Autonomous coding pipeline (Phase 2)
# ---------------------------------------------------------------------------
_pipeline_tasks: dict[str, dict[str, Any]] = {}


async def run_pipeline_background(
    task_id: str,
    issue_number: int,
    repo: str | None,
) -> None:
    """Runs the coding pipeline independently of the HTTP connection."""
    task = _pipeline_tasks[task_id]

    def _log(message: str) -> None:
        task["log"].append(message)

    try:
        task["status"] = "running"
        task["progress"] = 10
        _log(f"Fetching issue #{issue_number}…")

        issue = await asyncio.to_thread(get_issue, issue_number, repo_slug=repo)
        task["progress"] = 25
        _log(f"Issue #{issue_number}: {issue.get('title', '')}")

        result = await asyncio.to_thread(process_issue, issue, None, None)

        if result.get("success"):
            task["status"] = "completed"
            task["progress"] = 100
            _log(f"Pipeline completed — PR: {result.get('pr_url', 'n/a')}")
        else:
            task["status"] = "failed"
            task["progress"] = 100
            _log(f"Pipeline failed — {result.get('error', 'unknown error')}")
    except Exception as exc:
        task["status"] = "failed"
        task["progress"] = 100
        _log(f"Error: {exc}")
        logger.exception("Pipeline task %s failed", task_id)


@app.get("/pipeline/issues")
async def get_ready_issues():
    """Liste les issues GitHub prêtes à être traitées."""
    try:
        return list_ready_issues()
    except ValueError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


@app.post("/pipeline/run/{issue_number}")
async def run_pipeline(issue_number: int, repo: str | None = None):
    """Déclenche le pipeline sur une issue spécifique (repo=hub|naia|nomad)."""
    task_id = str(uuid.uuid4())
    _pipeline_tasks[task_id] = {
        "status": "starting",
        "log": [f"Pipeline queued for issue #{issue_number}"],
        "progress": 0,
        "issue_number": issue_number,
        "repo": repo,
    }
    asyncio.create_task(run_pipeline_background(task_id, issue_number, repo))
    return {
        "status": "started",
        "task_id": task_id,
        "issue": issue_number,
        "repo": repo,
    }


@app.get("/pipeline/status/{task_id}")
async def pipeline_status(task_id: str):
    """Retourne l'état d'une exécution pipeline (polling côté client)."""
    task = _pipeline_tasks.get(task_id)
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")
    return {
        "status": task["status"],
        "log": task["log"],
        "progress": task["progress"],
    }


@app.get("/costs/today")
async def costs_today():
    try:
        return get_daily_costs()
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.get("/costs/month")
async def costs_month():
    try:
        return get_monthly_costs()
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.get("/costs/week")
async def costs_week():
    try:
        return get_weekly_costs()
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


# ---------------------------------------------------------------------------
# Dashboard — WebSocket live updates
# ---------------------------------------------------------------------------
class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def broadcast(self, message: dict):
        for connection in list(self.active_connections):
            try:
                await connection.send_json(message)
            except Exception:
                self.disconnect(connection)


ws_manager = ConnectionManager()
_coo_agent_singleton: COOAgent | None = None


def _get_coo_agent() -> COOAgent:
    global _coo_agent_singleton
    if _coo_agent_singleton is None:
        _coo_agent_singleton = COOAgent()
    return _coo_agent_singleton


@app.websocket("/ws/coo")
async def websocket_coo(websocket: WebSocket):
    await ws_manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_json()
            await websocket.send_json({"type": "thinking", "message": "Analyse en cours…"})
            response = await asyncio.to_thread(
                _get_coo_agent().handle_instruction,
                data.get("message", ""),
            )
            await websocket.send_json({"type": "response", "message": response})
            await websocket.send_json({"type": "speaking", "message": response[:120]})
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)


@app.websocket("/ws/pipeline")
async def websocket_pipeline(websocket: WebSocket):
    await ws_manager.connect(websocket)
    try:
        while True:
            await asyncio.sleep(5)
            await websocket.send_json(
                {"type": "heartbeat", "message": "Pipeline actif — polling GitHub"}
            )
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)


@app.get("/brief/today")
async def get_brief_today():
    """Brief matinal formaté pour le dashboard."""
    try:
        briefing = await asyncio.to_thread(_get_coo_agent().get_daily_briefing)
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


@app.get("/github/prs")
async def get_github_prs():
    try:
        return get_open_prs()
    except ValueError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.get("/branches/app")
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


@app.get("/branches/gaming")
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


@app.get("/branches/robo")
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


@app.get("/eve/status")
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


# ---------------------------------------------------------------------------
# Projects
# ---------------------------------------------------------------------------
@app.get("/projects")
def list_projects(branch: str | None = None) -> list[dict[str, Any]]:
    db = get_supabase()
    filters = {"branch": branch} if branch else None
    return db.select("projects", filters=filters, order_by="name")


@app.get("/projects/{project_id}")
def get_project(project_id: str) -> dict[str, Any]:
    db = get_supabase()
    rows = db.select("projects", filters={"id": project_id})
    if not rows:
        raise HTTPException(status_code=404, detail="Project not found")
    return rows[0]


@app.post("/projects")
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


# ---------------------------------------------------------------------------
# Dev log
# ---------------------------------------------------------------------------
@app.post("/dev-log")
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


@app.get("/dev-log")
def list_dev_log(project_id: str, unused_only: bool = False) -> list[dict[str, Any]]:
    db = get_supabase()
    filters: dict[str, Any] = {"project_id": project_id}
    if unused_only:
        filters["used_for_content"] = False
    return db.select("dev_log", filters=filters, order_by="date", ascending=False)


# ---------------------------------------------------------------------------
# Tickets
# ---------------------------------------------------------------------------
PRIORITY_ORDER = {"critical": 0, "high": 1, "medium": 2, "low": 3}


@app.post("/tickets")
def create_ticket(body: TicketCreate) -> dict[str, Any]:
    db = get_supabase()
    return db.insert(
        "tickets",
        {
            "project_id": body.project_id,
            "type": body.type,
            "priority": body.priority,
            "title": body.title,
            "description": body.description,
            "source": body.source,
            "status": "open",
        },
    )


@app.get("/tickets")
def list_tickets(
    project_id: str | None = None,
    status: str | None = None,
    priority: list[str] | None = Query(None),
    ticket_type: list[str] | None = Query(None, alias="type"),
    limit: int = Query(default=50, le=200),
) -> list[dict[str, Any]]:
    db = get_supabase()
    filters: dict[str, Any] = {}
    if project_id:
        filters["project_id"] = project_id
    if status:
        filters["status"] = status

    tickets = db.select(
        "tickets",
        filters=filters or None,
        order_by="created_at",
        ascending=False,
        limit=limit * 3,
    )

    if priority:
        allowed = set(priority)
        tickets = [t for t in tickets if t.get("priority") in allowed]
    if ticket_type:
        allowed_types = set(ticket_type)
        tickets = [t for t in tickets if t.get("type") in allowed_types]

    # Priorité critique d'abord, puis date desc (tri stable)
    tickets.sort(key=lambda t: t.get("created_at") or "", reverse=True)
    tickets.sort(key=lambda t: PRIORITY_ORDER.get(t.get("priority", "medium"), 9))

    projects = {p["id"]: p["name"] for p in db.select("projects")}
    for ticket in tickets[:limit]:
        ticket["project_name"] = projects.get(ticket.get("project_id"), "Projet")

    return tickets[:limit]


@app.patch("/tickets/{ticket_id}")
def update_ticket(ticket_id: str, body: TicketUpdate) -> dict[str, Any]:
    db = get_supabase()
    rows = db.select("tickets", filters={"id": ticket_id})
    if not rows:
        raise HTTPException(status_code=404, detail="Ticket not found")

    values = body.model_dump(exclude_none=True)
    if not values:
        raise HTTPException(status_code=400, detail="Aucun champ à mettre à jour")
    return db.update("tickets", ticket_id, values)


@app.patch("/tickets/{ticket_id}/status")
def update_ticket_status(ticket_id: str, status: str) -> dict[str, Any]:
    allowed = {"open", "in_progress", "done", "wont_fix"}
    if status not in allowed:
        raise HTTPException(status_code=400, detail=f"status must be one of {allowed}")
    db = get_supabase()
    return db.update("tickets", ticket_id, {"status": status})


@app.post("/tickets/{ticket_id}/generate-cursor-prompt")
def generate_ticket_cursor_prompt(ticket_id: str) -> dict[str, Any]:
    settings = get_settings()
    if not settings.openrouter_api_key.strip():
        raise HTTPException(status_code=503, detail="OPENROUTER_API_KEY manquante")
    agent = SpecAgent()
    try:
        updated = agent.generate_cursor_prompt(ticket_id)
        return {"cursor_prompt": updated.get("cursor_prompt", ""), "ticket": updated}
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except Exception as exc:
        logger.exception("generate_cursor_prompt failed")
        raise HTTPException(status_code=500, detail=str(exc)) from exc


# ---------------------------------------------------------------------------
# Feedback
# ---------------------------------------------------------------------------
@app.post("/feedback")
def create_feedback(body: FeedbackCreate) -> dict[str, Any]:
    db = get_supabase()
    return db.insert(
        "feedback",
        {
            "project_id": body.project_id,
            "source": body.source,
            "content": body.content,
            "author": body.author,
            "rating": body.rating,
            "sentiment": body.sentiment,
            "status": "new",
        },
    )


@app.get("/feedback")
def list_feedback(
    project_id: str | None = None,
    status: str | None = None,
    limit: int = Query(default=50, le=200),
) -> list[dict[str, Any]]:
    db = get_supabase()
    filters: dict[str, Any] = {}
    if project_id:
        filters["project_id"] = project_id
    if status:
        filters["status"] = status
    rows = db.select(
        "feedback",
        filters=filters or None,
        order_by="created_at",
        ascending=False,
        limit=limit,
    )
    if rows and project_id is None:
        projects = {p["id"]: p["name"] for p in db.select("projects")}
        for row in rows:
            row["project_name"] = projects.get(row.get("project_id"), "Projet")
    return rows


# ---------------------------------------------------------------------------
# Roadmap
# ---------------------------------------------------------------------------
ROADMAP_PRIORITY_ORDER = {"critical": 0, "high": 1, "medium": 2, "low": 3}
ROADMAP_STATUSES_ALLOWED = frozenset({"idea", "planned", "in_progress", "done"})


def _normalize_roadmap_row(row: dict[str, Any]) -> dict[str, Any]:
    """Map legacy DB values (int priority, sprint) to the v2 schema."""
    priority = row.get("priority", "medium")
    if isinstance(priority, (int, float)):
        n = int(priority)
        row["priority"] = (
            "critical" if n >= 8 else "high" if n >= 6 else "medium" if n >= 3 else "low"
        )
    elif isinstance(priority, str) and priority.isdigit():
        n = int(priority)
        row["priority"] = (
            "critical" if n >= 8 else "high" if n >= 6 else "medium" if n >= 3 else "low"
        )
    elif priority not in ROADMAP_PRIORITY_ORDER:
        row["priority"] = "medium"

    status = row.get("status", "planned")
    if status not in ROADMAP_STATUSES_ALLOWED:
        row["status"] = "planned"

    if not row.get("phase") and row.get("sprint"):
        row["phase"] = row["sprint"]

    return row


def _enrich_roadmap_items(
    db: Any, items: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    if not items:
        return items
    projects = {p["id"]: p["name"] for p in db.select("projects")}
    for row in items:
        _normalize_roadmap_row(row)
        row["project_name"] = projects.get(row.get("project_id"), "Projet")
    return items


def _sort_roadmap_items(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    # critical first, then earliest due_date (nulls last)
    items.sort(
        key=lambda r: r.get("due_date") or "9999-12-31",
    )
    items.sort(
        key=lambda r: ROADMAP_PRIORITY_ORDER.get(
            str(r.get("priority", "medium")), 9
        ),
    )
    return items


@app.get("/roadmap")
def list_roadmap(
    status: str | None = None,
    project_id: str | None = None,
    priority: list[str] | None = Query(None),
    phase: str | None = None,
) -> list[dict[str, Any]]:
    db = get_supabase()
    filters: dict[str, Any] = {}
    if status:
        filters["status"] = status
    if project_id:
        filters["project_id"] = project_id
    if phase:
        filters["phase"] = phase

    items = db.select(
        "roadmap",
        filters=filters or None,
        order_by="created_at",
        ascending=False,
    )

    if priority:
        allowed = set(priority)
        items = [r for r in items if r.get("priority") in allowed]

    return _enrich_roadmap_items(db, _sort_roadmap_items(items))


@app.post("/roadmap")
def create_roadmap_item(body: RoadmapCreate) -> dict[str, Any]:
    db = get_supabase()
    row = db.insert(
        "roadmap",
        {
            "project_id": body.project_id,
            "title": body.title,
            "description": body.description,
            "status": body.status,
            "priority": body.priority,
            "phase": body.phase or "",
            "due_date": body.due_date.isoformat() if body.due_date else None,
        },
    )
    return _enrich_roadmap_items(db, [row])[0]


@app.patch("/roadmap/{item_id}")
def update_roadmap_item(item_id: str, body: RoadmapUpdate) -> dict[str, Any]:
    db = get_supabase()
    rows = db.select("roadmap", filters={"id": item_id})
    if not rows:
        raise HTTPException(status_code=404, detail="Roadmap item not found")

    values = body.model_dump(exclude_none=True)
    if "due_date" in values and values["due_date"] is not None:
        values["due_date"] = values["due_date"].isoformat()
    if not values:
        raise HTTPException(status_code=400, detail="Aucun champ à mettre à jour")

    updated = db.update("roadmap", item_id, values)
    return _enrich_roadmap_items(db, [updated])[0]


@app.delete("/roadmap/{item_id}")
def delete_roadmap_item(item_id: str) -> dict[str, str]:
    db = get_supabase()
    rows = db.select("roadmap", filters={"id": item_id})
    if not rows:
        raise HTTPException(status_code=404, detail="Roadmap item not found")
    db.delete("roadmap", item_id)
    return {"status": "deleted", "id": item_id}


def _quick_capture_title(content: str, max_len: int = 120) -> str:
    """First non-empty line becomes the item title."""
    for line in content.strip().splitlines():
        stripped = line.strip()
        if stripped:
            return stripped[:max_len]
    return "Capture rapide"


@app.post("/quick-capture")
def quick_capture(body: QuickCaptureRequest) -> dict[str, Any]:
    """Route a Quick Capture payload to tickets, brainstorm, roadmap, or quick_notes."""
    db = get_supabase()
    content = body.content.strip()
    if not content:
        raise HTTPException(status_code=400, detail="Le contenu ne peut pas être vide")

    title = _quick_capture_title(content)
    priority = body.priority or "medium"

    if body.type == "ticket":
        row = db.insert(
            "tickets",
            {
                "project_id": body.project_id,
                "type": "bug",
                "priority": priority,
                "title": title,
                "description": content,
                "source": "quick_capture",
                "status": "open",
            },
        )
        return {
            "id": row["id"],
            "type": "ticket",
            "redirect_url": f"/tickets?id={row['id']}",
        }

    if body.type == "idea":
        capture_id = str(uuid.uuid4())
        row = db.insert(
            "brainstorm_summaries",
            {
                "project_id": body.project_id,
                "session_id": f"quick-capture-{capture_id}",
                "session_number": 0,
                "title": title,
                "summary": content,
                "key_ideas": [title],
            },
        )
        return {
            "id": row["id"],
            "type": "idea",
            "redirect_url": "/brainstorm",
        }

    if body.type == "roadmap":
        row = db.insert(
            "roadmap",
            {
                "project_id": body.project_id,
                "title": title,
                "description": content,
                "status": "idea",
                "priority": priority,
            },
        )
        return {
            "id": row["id"],
            "type": "roadmap",
            "redirect_url": f"/roadmap?id={row['id']}",
        }

    if body.type == "note":
        row = db.insert(
            "quick_notes",
            {
                "project_id": body.project_id,
                "content": content,
            },
        )
        return {
            "id": row["id"],
            "type": "note",
            "redirect_url": "/",
        }

    raise HTTPException(status_code=400, detail=f"Type inconnu : {body.type}")


@app.post("/roadmap/from-ticket/{ticket_id}")
def create_roadmap_from_ticket(ticket_id: str) -> dict[str, Any]:
    db = get_supabase()
    tickets = db.select("tickets", filters={"id": ticket_id})
    if not tickets:
        raise HTTPException(status_code=404, detail="Ticket not found")
    ticket = tickets[0]

    existing = db.select(
        "roadmap",
        filters={"linked_ticket_id": ticket_id},
    )
    if existing:
        raise HTTPException(
            status_code=409,
            detail="Un item roadmap existe déjà pour ce ticket",
        )

    priority = ticket.get("priority", "medium")
    if priority not in ROADMAP_PRIORITY_ORDER:
        priority = "medium"

    row = db.insert(
        "roadmap",
        {
            "project_id": ticket["project_id"],
            "title": ticket["title"],
            "description": ticket.get("description", ""),
            "status": "planned",
            "priority": priority,
            "linked_ticket_id": ticket_id,
        },
    )
    return _enrich_roadmap_items(db, [row])[0]


# ---------------------------------------------------------------------------
# Posts queue
# ---------------------------------------------------------------------------
@app.get("/posts")
def list_posts(
    project_id: str | None = None,
    status: str | None = None,
    platform: str | None = None,
) -> list[dict[str, Any]]:
    db = get_supabase()
    filters: dict[str, Any] = {}
    if project_id:
        filters["project_id"] = project_id
    if status:
        filters["status"] = status
    if platform:
        filters["platform"] = platform
    return db.select(
        "posts_queue",
        filters=filters or None,
        order_by="created_at",
        ascending=False,
    )


@app.patch("/posts/{post_id}")
def update_post(post_id: str, body: PostUpdate) -> dict[str, Any]:
    agent = ContentAgent()
    try:
        payload = body.model_dump(exclude_none=True)
        return agent.update_post(post_id, payload)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@app.patch("/posts/{post_id}/approve")
def approve_post(post_id: str) -> dict[str, Any]:
    agent = ContentAgent()
    return agent.approve_post(post_id)


# ---------------------------------------------------------------------------
# Analytics & transactions
# ---------------------------------------------------------------------------
def _fetch_all_analytics(db, project_id: str | None = None) -> list[dict[str, Any]]:
    filters = {"project_id": project_id} if project_id else None
    return db.select(
        "analytics",
        filters=filters,
        order_by="date",
        ascending=True,
        limit=2000,
    )


def _fetch_transactions(db, project_id: str | None = None) -> list[dict[str, Any]]:
    filters = {"project_id": project_id} if project_id else None
    return db.select(
        "transactions",
        filters=filters,
        order_by="date",
        ascending=True,
        limit=2000,
    )


def _kpi_metric(
    rows: list[dict[str, Any]],
    metric_name: str,
    project_id: str | None,
    use_sum_in_month: bool = False,
) -> dict[str, Any]:
    """Calcule valeur du mois courant + variation vs mois précédent."""
    cur_start, cur_end = month_bounds()
    prev_start, prev_end = previous_month_bounds()

    if use_sum_in_month:
        current = sum_metric_in_range(rows, metric_name, cur_start, cur_end, project_id)
        previous = sum_metric_in_range(rows, metric_name, prev_start, prev_end, project_id)
    else:
        cur_latest = latest_values_by_project(rows, metric_name, cur_end)
        prev_latest = latest_values_by_project(rows, metric_name, prev_end)
        if project_id:
            current = cur_latest.get(project_id)
            previous = prev_latest.get(project_id)
        else:
            current = sum(cur_latest.values()) if cur_latest else None
            previous = sum(prev_latest.values()) if prev_latest else None

    return {
        "value": current if current is not None else None,
        "change_pct": pct_change(current, previous),
    }


@app.get("/analytics")
def list_analytics(
    project_id: str | None = None,
    metric_name: str | None = None,
    period: str = Query(default="30d"),
    start_date: date | None = None,
    end_date: date | None = None,
) -> list[dict[str, Any]]:
    db = get_supabase()
    if start_date and end_date:
        start, end = start_date, end_date
    else:
        start, end = parse_period(period)

    rows = _fetch_all_analytics(db, project_id)
    if metric_name:
        rows = [r for r in rows if r.get("metric_name") == metric_name]
    rows = filter_by_date_range(rows, start, end)

    projects = {p["id"]: p["name"] for p in db.select("projects")}
    for row in rows:
        row["project_name"] = projects.get(row.get("project_id"), "Projet")
    return rows


@app.get("/analytics/summary")
def analytics_summary(project_id: str | None = None) -> dict[str, Any]:
    db = get_supabase()
    rows = _fetch_all_analytics(db, project_id)
    tx_rows = _fetch_transactions(db, project_id)

    cur_start, cur_end = month_bounds()
    prev_start, prev_end = previous_month_bounds()

    revenue_cur = sum(
        float(t["amount"])
        for t in tx_rows
        if t.get("type") in ("revenue", "income")
        and cur_start <= date.fromisoformat(str(t["date"])[:10]) <= cur_end
    )
    revenue_prev = sum(
        float(t["amount"])
        for t in tx_rows
        if t.get("type") in ("revenue", "income")
        and prev_start <= date.fromisoformat(str(t["date"])[:10]) <= prev_end
    )

    return {
        "downloads": _kpi_metric(rows, "downloads", project_id, use_sum_in_month=True),
        "subscriptions": _kpi_metric(rows, "subscriptions", project_id),
        "mrr": _kpi_metric(rows, "mrr", project_id),
        "churn": _kpi_metric(rows, "churn", project_id),
        "web_visitors": _kpi_metric(rows, "web_visitors", project_id, use_sum_in_month=True),
        "revenue_month": {
            "value": revenue_cur if revenue_cur else None,
            "change_pct": pct_change(revenue_cur, revenue_prev),
        },
    }


@app.get("/analytics/revenue")
def analytics_revenue(
    project_id: str | None = None,
    period: str = Query(default="30d"),
) -> dict[str, Any]:
    db = get_supabase()
    start, end = parse_period(period)
    tx_rows = filter_by_date_range(_fetch_transactions(db, project_id), start, end)
    analytics_rows = filter_by_date_range(_fetch_all_analytics(db, project_id), start, end)

    months: dict[str, dict[str, float]] = {}

    for tx in tx_rows:
        d = date.fromisoformat(str(tx["date"])[:10])
        key = d.strftime("%Y-%m")
        bucket = months.setdefault(key, {"revenue": 0.0, "expense": 0.0, "mrr": 0.0})
        if tx.get("type") in ("revenue", "income"):
            bucket["revenue"] += float(tx["amount"])
        else:
            bucket["expense"] += float(tx["amount"])

    for row in analytics_rows:
        if row.get("metric_name") != "mrr":
            continue
        d = date.fromisoformat(str(row["date"])[:10])
        key = d.strftime("%Y-%m")
        bucket = months.setdefault(key, {"revenue": 0.0, "expense": 0.0, "mrr": 0.0})
        bucket["mrr"] = max(bucket["mrr"], float(row["value"]))

    series = [
        {"month": k, **v}
        for k, v in sorted(months.items())
    ]
    return {"months": series}


@app.post("/analytics")
def create_analytics_metric(body: AnalyticsCreate) -> dict[str, Any]:
    db = get_supabase()
    return db.insert(
        "analytics",
        {
            "project_id": body.project_id,
            "metric_name": body.metric_name,
            "value": body.value,
            "date": (body.record_date or date.today()).isoformat(),
            "source": body.source,
        },
    )


@app.post("/transactions")
def create_transaction(body: TransactionCreate) -> dict[str, Any]:
    db = get_supabase()
    tx_type = "income" if body.type == "revenue" else body.type
    return db.insert(
        "transactions",
        {
            "project_id": body.project_id,
            "type": tx_type,
            "amount": body.amount,
            "currency": body.currency,
            "category": body.category,
            "description": body.description,
            "date": (body.transaction_date or date.today()).isoformat(),
            "is_recurring": body.is_recurring,
            "recurrence": body.recurrence,
        },
    )


# ---------------------------------------------------------------------------
# FAQ & SAV
# ---------------------------------------------------------------------------
@app.post("/faq")
def create_faq(body: FAQCreate) -> dict[str, Any]:
    bot = SAVBot()
    return bot.add_faq_entry(body.project_id, body.question, body.answer, body.tags)


@app.get("/faq")
def list_faq(project_id: str) -> list[dict[str, Any]]:
    bot = SAVBot()
    return bot.get_faq(project_id)


@app.post("/sav/ask")
def sav_ask(body: SAVQuestion) -> dict[str, Any]:
    bot = SAVBot()
    return bot.handle_question(body.project_id, body.question, body.author)


# ---------------------------------------------------------------------------
# Agent endpoints
# ---------------------------------------------------------------------------
# ---------------------------------------------------------------------------
# Daily briefing
# ---------------------------------------------------------------------------
@app.get("/briefing/today")
def briefing_today() -> dict[str, Any]:
    db = get_supabase()
    today = date.today()
    row = get_briefing_for_date(db, today)
    if row is None:
        row = generate_and_store_daily_briefing()
    return row


@app.get("/briefing/history")
def briefing_history(limit: int = Query(default=30, ge=1, le=100)) -> list[dict[str, Any]]:
    db = get_supabase()
    response = (
        db.table("daily_briefings")
        .select("*")
        .order("date", desc=True)
        .limit(limit)
        .execute()
    )
    return response.data or []


@app.post("/briefing/generate")
def briefing_generate() -> dict[str, Any]:
    try:
        return generate_and_store_daily_briefing(replace_existing=True)
    except Exception as exc:
        logger.exception("briefing_generate failed")
        raise HTTPException(status_code=500, detail=str(exc)) from exc


# ---------------------------------------------------------------------------
# Releases — App Store / Google Play / CHANGELOG generator
# ---------------------------------------------------------------------------
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


@app.get("/releases")
def list_releases(project_id: str | None = None) -> list[dict[str, Any]]:
    db = get_supabase()
    query = db.table("releases").select("*").order("created_at", desc=True)
    if project_id:
        query = query.eq("project_id", project_id)
    response = query.execute()
    return _enrich_releases_with_project_names(db, response.data or [])


@app.get("/releases/{release_id}")
def get_release(release_id: str) -> dict[str, Any]:
    db = get_supabase()
    rows = db.select("releases", filters={"id": release_id})
    if not rows:
        raise HTTPException(status_code=404, detail="Release introuvable")
    enriched = _enrich_releases_with_project_names(db, rows)
    return enriched[0]


@app.post("/releases/generate")
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


@app.patch("/releases/{release_id}")
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


@app.delete("/releases/{release_id}")
def delete_release(release_id: str) -> dict[str, bool]:
    db = get_supabase()
    existing = db.select("releases", filters={"id": release_id})
    if not existing:
        raise HTTPException(status_code=404, detail="Release introuvable")
    db.delete("releases", release_id)
    return {"ok": True}


@app.post("/agents/coo/briefing")
def coo_briefing() -> dict[str, str]:
    agent = COOAgent()
    briefing = agent.run_daily_briefing()
    return {"briefing": briefing}


@app.post("/agents/coo/instruction", response_model=COOInstructionResponse)
def coo_instruction(body: COOInstruction) -> COOInstructionResponse:
    result = _get_coo_agent().process_message(body.instruction, body.project)
    return COOInstructionResponse(**result)


@app.post("/webhook/telegram")
async def telegram_webhook(request: Request) -> dict[str, bool]:
    """Receives Telegram updates (webhook mode — production)."""
    settings = get_settings()
    if not settings.telegram_bot_token:
        raise HTTPException(status_code=503, detail="Telegram bot not configured")

    update_data = await request.json()
    await get_telegram_bot().process_update(update_data)
    return {"ok": True}


@app.post("/agents/pm/triage/{project_id}")
def pm_triage(project_id: str) -> dict[str, Any]:
    agent = PMAgent()
    return agent.triage_project(project_id)


@app.post("/agents/qa/analyze/{project_id}")
def qa_analyze(project_id: str) -> dict[str, Any]:
    agent = QAAgent()
    return agent.analyze_feedback_batch(project_id)


@app.post("/agents/content/generate")
def content_generate(body: ContentGenerateRequest) -> dict[str, Any]:
    agent = ContentAgent()
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


@app.post("/agents/content/generate/{project_id}")
def content_generate_legacy(project_id: str) -> dict[str, Any]:
    agent = ContentAgent()
    posts = agent.generate_from_dev_logs(project_id)
    return {"posts_created": len(posts), "posts": posts}


@app.post("/agents/brainstorm")
def brainstorm(body: BrainstormRequest) -> dict[str, Any]:
    agent = BrainstormAgent()
    return agent.brainstorm(body.project_id, body.topic, body.context_notes)


@app.post("/agents/brainstorm/chat")
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
        return agent.chat(body.message, body.project_id, body.session_id)
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


@app.get("/brainstorm/sessions")
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


@app.post("/brainstorm/sessions/{session_id}/summarize")
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


@app.get("/brainstorm/sessions/{session_id}/summary")
def brainstorm_session_summary(session_id: str) -> dict[str, Any]:
    """Retourne le compte-rendu existant d'une session."""
    agent = BrainstormAgent()
    summary = agent.get_summary_for_session(session_id)
    if not summary:
        raise HTTPException(status_code=404, detail="Aucun compte-rendu pour cette session")
    return summary


@app.post("/brainstorm/summaries/reveal")
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


@app.get("/brainstorm/sessions/{session_id}")
def brainstorm_session(session_id: str) -> dict[str, Any]:
    agent = BrainstormAgent()
    try:
        return agent.get_session(session_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@app.get("/brainstorm/welcome")
def brainstorm_welcome() -> dict[str, str]:
    return {"message": WELCOME_MESSAGE}


@app.post("/agents/spec/{ticket_id}")
def spec_generate(ticket_id: str) -> dict[str, Any]:
    agent = SpecAgent()
    return agent.generate_cursor_prompt(ticket_id)


@app.get("/agents/logs")
def agent_logs(limit: int = Query(default=50, le=200)) -> list[dict[str, Any]]:
    db = get_supabase()
    return db.select("agent_logs", order_by="created_at", ascending=False, limit=limit)


# === BRAND KIT ===
_IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp", ".gif"}
_REPO_ROOT = BRAND_KITS_ROOT.parent.resolve()
_FULL_KIT_FORMAT_COUNT = len(ALL_FORMAT_NAMES)


class BrandGenerateKitRequest(BaseModel):
    kit_id: str | None = None
    project_id: str
    formats: list[str] | None = None
    upload_path: str | None = None
    analysis: dict[str, Any] | None = None


class BrandOpenFolderRequest(BaseModel):
    kit_id: str


class BrandRefineSegmentsRequest(BaseModel):
    elements: list[BrandElement]
    labels: list[str] | None = None
    force_bbox: bool = Field(
        default=True,
        description="When true, skip OpenCV panel snap and use bbox as-is.",
    )


def _resolve_repo_path(relative_path: str) -> Path:
    normalized = relative_path.replace("\\", "/").lstrip("/")
    if ".." in normalized.split("/"):
        raise HTTPException(status_code=400, detail="Chemin invalide")
    file_path = (_REPO_ROOT / normalized).resolve()
    if not str(file_path).startswith(str(_REPO_ROOT)):
        raise HTTPException(status_code=400, detail="Chemin invalide")
    return file_path


def _kit_project_dir(assets_path: str) -> Path:
    return _resolve_repo_path(assets_path)


def _create_kit_zip(assets: dict[str, str], report_path: str | None) -> io.BytesIO:
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as archive:
        for format_name, rel_path in sorted(assets.items()):
            full_path = _resolve_repo_path(rel_path)
            if full_path.is_file():
                suffix = full_path.suffix or ".png"
                archive.write(full_path, arcname=f"{format_name}{suffix}")
        if report_path:
            report_full = _resolve_repo_path(report_path)
            if report_full.is_file():
                archive.write(report_full, arcname=REPORT_FILENAME)
    buffer.seek(0)
    return buffer


def _load_brand_kit(kit_id: str) -> dict[str, Any]:
    db = get_supabase()
    rows = db.select("brand_kits", filters={"id": kit_id})
    if not rows:
        raise HTTPException(status_code=404, detail="Kit introuvable")
    return rows[0]


@app.post("/brand/analyze")
async def brand_analyze(
    file: UploadFile = File(...),
    project_id: str = Form(...),
) -> dict[str, Any]:
    """Upload brand image, run GPT-4V metadata + Grounding DINO bboxes + K-means."""
    db = get_supabase()
    projects = db.select("projects", filters={"id": project_id})
    if not projects:
        raise HTTPException(status_code=404, detail="Projet introuvable")

    project = projects[0]

    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Le fichier doit être une image")

    ensure_brand_kit_dirs()

    ext = Path(file.filename or "").suffix.lower()
    if ext not in _IMAGE_EXTENSIONS:
        ext = ".png" if file.content_type == "image/png" else ".jpg"

    upload_path = BRAND_KITS_ROOT / "uploads" / f"{uuid.uuid4()}{ext}"
    upload_path.write_bytes(await file.read())

    # Same resized image for DINO bbox + OpenCV crop (spec pipeline rule).
    processed_path, (img_w, img_h) = prepare_brand_image(str(upload_path))

    llm_analysis = analyze_brand_image(processed_path)
    kmeans_colors = extract_kmeans_colors(processed_path)
    merged_colors = merge_palettes(llm_analysis.colors, kmeans_colors)

    analysis = llm_analysis.model_copy(update={"colors": merged_colors})

    project_slug = BrainstormAgent.project_folder_slug(project["name"], project["id"])
    assets_path = f"brand_kits/{project_slug}"
    project_dir = BRAND_KITS_ROOT / project_slug
    segments_dir = project_dir / "segments"
    isolated_dir = project_dir / "isolated"

    segment_paths = segment_elements(
        processed_path,
        analysis.elements,
        segments_dir=str(segments_dir),
    )
    isolated_assets = generate_isolated_assets(
        processed_path,
        analysis,
        str(isolated_dir),
    )

    relative_upload = str(Path(processed_path).relative_to(_REPO_ROOT)).replace("\\", "/")
    analysis_payload = analysis.model_dump(mode="json")
    analysis_payload["segment_paths"] = segment_paths
    analysis_payload["isolated_assets"] = isolated_assets
    analysis_payload["upload_path"] = relative_upload
    analysis_payload["source_size"] = {"width": img_w, "height": img_h}

    kit_id: str | None = None
    try:
        kit_row = db.insert(
            "brand_kits",
            {
                "project_id": project_id,
                "brand_name": analysis.brand_name,
                "analysis": analysis_payload,
                "assets_path": assets_path,
                "formats_generated": [],
            },
        )
        kit_id = kit_row["id"]
    except Exception as exc:
        # Table may not exist yet — analysis still usable in UI
        logger.warning("brand_kits persist skipped: %s", exc)

    return {
        "kit_id": kit_id,
        "analysis": analysis_payload,
        "upload_path": relative_upload,
        "segment_paths": segment_paths,
        "isolated_assets": isolated_assets,
    }


@app.post("/brand/generate-kit")
def brand_generate_kit(body: BrandGenerateKitRequest) -> dict[str, Any]:
    """Generate all kit formats, write BRAND_KIT.md, update Supabase."""
    db = get_supabase()
    kit: dict[str, Any] | None = None
    analysis_raw: dict[str, Any]
    assets_path: str
    kit_id: str

    if body.kit_id:
        kit = _load_brand_kit(body.kit_id)
        if kit["project_id"] != body.project_id:
            raise HTTPException(status_code=400, detail="project_id ne correspond pas au kit")
        analysis_raw = kit["analysis"]
        assets_path = kit["assets_path"]
        kit_id = body.kit_id
    else:
        if not body.upload_path or not body.analysis:
            raise HTTPException(
                status_code=400,
                detail="kit_id ou (upload_path + analysis) requis",
            )
        projects = db.select("projects", filters={"id": body.project_id})
        if not projects:
            raise HTTPException(status_code=404, detail="Projet introuvable")
        project = projects[0]
        project_slug = BrainstormAgent.project_folder_slug(project["name"], project["id"])
        assets_path = f"brand_kits/{project_slug}"
        analysis_raw = {**body.analysis, "upload_path": body.upload_path}

        brand_name = analysis_raw.get("brand_name") or "Brand"
        try:
            kit_row = db.insert(
                "brand_kits",
                {
                    "project_id": body.project_id,
                    "brand_name": brand_name,
                    "analysis": analysis_raw,
                    "assets_path": assets_path,
                    "formats_generated": [],
                },
            )
            kit_id = kit_row["id"]
        except Exception as exc:
            logger.warning("brand_kits insert on generate skipped: %s", exc)
            kit_id = str(uuid.uuid4())

    upload_path = analysis_raw.get("upload_path")
    if not upload_path:
        raise HTTPException(status_code=400, detail="upload_path manquant dans l'analyse")

    image_path = _resolve_repo_path(upload_path)
    if not image_path.is_file():
        raise HTTPException(status_code=404, detail="Image source introuvable")

    brand_data = BrandAnalysis.model_validate(analysis_raw)
    project_dir = _kit_project_dir(assets_path)

    generated = generate_full_kit(
        str(image_path),
        brand_data,
        str(project_dir),
        formats=body.formats,
    )

    report_path = generate_brand_report(brand_data, generated, str(project_dir))
    formats_generated = sorted(set(generated.keys()))
    updated_analysis = {
        **analysis_raw,
        "generated_assets": generated,
        "report_path": report_path,
    }

    try:
        if kit is not None or body.kit_id:
            db.update(
                "brand_kits",
                kit_id,
                {
                    "formats_generated": formats_generated,
                    "analysis": updated_analysis,
                },
            )
        elif body.upload_path and body.analysis:
            db.update(
                "brand_kits",
                kit_id,
                {
                    "formats_generated": formats_generated,
                    "analysis": updated_analysis,
                },
            )
    except Exception as exc:
        logger.warning("brand_kits update skipped: %s", exc)

    return {
        "kit_id": kit_id,
        "assets": generated,
        "report_path": report_path,
        "zip_url": f"/brand/kits/{kit_id}/download",
        "formats_generated": formats_generated,
    }


@app.get("/brand/kits")
def brand_list_kits(
    project_id: str | None = Query(default=None),
) -> list[dict[str, Any]]:
    """List brand kits, optionally filtered by project."""
    db = get_supabase()
    filters = {"project_id": project_id} if project_id else None
    rows = db.select(
        "brand_kits",
        filters=filters,
        order_by="created_at",
        ascending=False,
    )
    return [
        {
            "id": row["id"],
            "project_id": row["project_id"],
            "brand_name": row["brand_name"],
            "assets_path": row["assets_path"],
            "formats_generated": row.get("formats_generated") or [],
            "is_complete": len(row.get("formats_generated") or []) >= _FULL_KIT_FORMAT_COUNT,
            "created_at": row.get("created_at"),
            "updated_at": row.get("updated_at"),
        }
        for row in rows
    ]


@app.get("/brand/kits/{kit_id}")
def brand_get_kit(kit_id: str) -> dict[str, Any]:
    """Return full kit record including analysis."""
    kit = _load_brand_kit(kit_id)
    analysis = kit["analysis"]
    generated_assets = analysis.get("generated_assets") or analysis.get("isolated_assets") or {}
    return {
        "id": kit["id"],
        "project_id": kit["project_id"],
        "brand_name": kit["brand_name"],
        "analysis": analysis,
        "assets_path": kit["assets_path"],
        "formats_generated": kit.get("formats_generated") or [],
        "generated_assets": generated_assets,
        "report_path": analysis.get("report_path"),
        "upload_path": analysis.get("upload_path"),
        "segment_paths": analysis.get("segment_paths") or {},
        "isolated_assets": analysis.get("isolated_assets") or {},
        "is_complete": len(kit.get("formats_generated") or []) >= _FULL_KIT_FORMAT_COUNT,
        "created_at": kit.get("created_at"),
        "updated_at": kit.get("updated_at"),
    }


@app.get("/brand/kits/{kit_id}/download")
def brand_download_kit(kit_id: str) -> StreamingResponse:
    """Stream a ZIP archive of all generated kit assets."""
    kit = _load_brand_kit(kit_id)
    analysis = kit["analysis"]
    assets: dict[str, str] = analysis.get("generated_assets") or analysis.get("isolated_assets") or {}
    if not assets:
        raise HTTPException(status_code=404, detail="Aucun asset généré pour ce kit")

    report_path = analysis.get("report_path")
    buffer = _create_kit_zip(assets, report_path)
    brand_slug = kit["brand_name"].replace(" ", "_").lower()
    filename = f"brand_kit_{brand_slug}.zip"

    return StreamingResponse(
        buffer,
        media_type="application/zip",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@app.post("/brand/kits/{kit_id}/refine-segments")
def brand_refine_segments(
    kit_id: str,
    body: BrandRefineSegmentsRequest,
) -> dict[str, Any]:
    """Re-crop segments after manual bbox adjustment — no LLM re-run."""
    kit = _load_brand_kit(kit_id)
    analysis_raw: dict[str, Any] = dict(kit["analysis"])
    upload_path = analysis_raw.get("upload_path")
    if not upload_path:
        raise HTTPException(status_code=400, detail="upload_path manquant dans l'analyse")

    image_path = _resolve_repo_path(upload_path)
    if not image_path.is_file():
        raise HTTPException(status_code=404, detail="Image source introuvable")

    use_panel_snap = not body.force_bbox
    labels_filter = set(body.labels) if body.labels else None

    brand_data = BrandAnalysis.model_validate(
        {**analysis_raw, "elements": [el.model_dump() for el in body.elements]}
    )
    project_dir = _kit_project_dir(kit["assets_path"])
    segments_dir = project_dir / "segments"
    isolated_dir = project_dir / "isolated"

    segment_paths = segment_elements(
        str(image_path),
        brand_data.elements,
        segments_dir=str(segments_dir),
        use_panel_snap=use_panel_snap,
        labels_filter=labels_filter,
        existing_paths=analysis_raw.get("segment_paths") or {},
    )
    isolated_assets = generate_isolated_assets(
        str(image_path),
        brand_data,
        str(isolated_dir),
        use_panel_snap=use_panel_snap,
    )

    updated_analysis = {
        **analysis_raw,
        "elements": [el.model_dump() for el in body.elements],
        "segment_paths": segment_paths,
        "isolated_assets": isolated_assets,
    }

    db = get_supabase()
    try:
        db.update(
            "brand_kits",
            kit_id,
            {"analysis": updated_analysis, "brand_name": brand_data.brand_name},
        )
    except Exception as exc:
        logger.warning("brand_kits refine update skipped: %s", exc)

    return {
        "kit_id": kit_id,
        "analysis": updated_analysis,
        "segment_paths": segment_paths,
        "isolated_assets": isolated_assets,
    }


@app.post("/brand/open-folder")
def brand_open_folder(body: BrandOpenFolderRequest) -> dict[str, bool]:
    """Open the kit folder in Windows Explorer."""
    kit = _load_brand_kit(body.kit_id)
    folder = _kit_project_dir(kit["assets_path"])
    if not folder.is_dir():
        raise HTTPException(status_code=404, detail="Dossier introuvable")
    subprocess.Popen(["explorer", str(folder)])
    return {"ok": True}


@app.get("/brand/assets")
async def brand_asset(path: str = Query(..., min_length=1)) -> FileResponse:
    """Serve a brand kit file by repo-relative path (e.g. brand_kits/slug/isolated/symbol_transparent.png)."""
    normalized = path.replace("\\", "/").lstrip("/")
    if ".." in normalized.split("/"):
        raise HTTPException(status_code=400, detail="Chemin invalide")

    repo_root = BRAND_KITS_ROOT.parent.resolve()
    file_path = (repo_root / normalized).resolve()

    if not str(file_path).startswith(str(repo_root)):
        raise HTTPException(status_code=400, detail="Chemin invalide")
    if not file_path.is_file():
        raise HTTPException(status_code=404, detail="Asset introuvable")

    return FileResponse(file_path)


# ---------------------------------------------------------------------------
# Beta tester portal
# ---------------------------------------------------------------------------
@app.get("/beta/info/{project_slug}")
def beta_info(project_slug: str) -> dict[str, Any]:
    db = get_supabase()
    project = resolve_project_by_slug(db, project_slug)
    version = latest_app_version(db, project["id"])
    return {
        "project_id": project["id"],
        "project_name": project["name"],
        "project_slug": project_slug_for(project),
        "app_version": version,
        "test_instructions": project.get("description") or "",
        "status": project.get("status"),
    }


@app.post("/beta/register")
def beta_register(body: BetaRegisterRequest) -> dict[str, Any]:
    db = get_supabase()
    project = resolve_project_by_slug(db, body.project_slug)
    email = body.email.strip().lower()

    existing = db.select(
        "beta_testers",
        filters={"project_id": project["id"], "email": email},
    )
    if existing:
        tester = db.update(
            "beta_testers",
            existing[0]["id"],
            {
                "first_name": body.first_name.strip(),
                "device": body.device,
                "os_version": body.os_version,
                "app_version": body.app_version,
            },
        )
    else:
        tester = db.insert(
            "beta_testers",
            {
                "project_id": project["id"],
                "email": email,
                "first_name": body.first_name.strip(),
                "device": body.device,
                "os_version": body.os_version,
                "app_version": body.app_version,
            },
        )

    token = create_tester_token(tester["id"], project["id"])
    return {
        "tester_id": tester["id"],
        "token": token,
        "first_name": tester.get("first_name"),
        "project_name": project["name"],
        "app_version": tester.get("app_version") or latest_app_version(db, project["id"]),
    }


@app.post("/beta/feedback")
def beta_submit_feedback(
    body: BetaFeedbackRequest,
    auth: dict[str, str] = Depends(_beta_tester_auth),
) -> dict[str, Any]:
    db = get_supabase()
    project = resolve_project_by_slug(db, body.project_slug)
    if auth["project_id"] != project["id"]:
        raise HTTPException(status_code=403, detail="Token non valide pour ce projet")

    tester = get_tester_or_404(db, auth["tester_id"])
    if tester["project_id"] != project["id"]:
        raise HTTPException(status_code=403, detail="Testeuse non inscrite à ce projet")

    screenshot_url: str | None = None
    if body.screenshot_base64:
        try:
            screenshot_url = upload_screenshot(db, body.screenshot_base64, project["id"])
        except Exception as exc:
            logger.exception("beta screenshot upload failed")
            raise HTTPException(status_code=400, detail="Échec upload screenshot") from exc

    ticket = create_feedback_ticket(
        db,
        project_id=project["id"],
        feedback_type=body.type,
        severity=body.severity,
        title=body.title.strip(),
        description=body.description.strip(),
        tester=tester,
    )

    feedback = db.insert(
        "beta_feedback",
        {
            "tester_id": tester["id"],
            "project_id": project["id"],
            "type": body.type,
            "title": body.title.strip(),
            "description": body.description.strip(),
            "screenshot_url": screenshot_url,
            "severity": body.severity,
            "ticket_id": ticket["id"],
        },
    )

    db.update(
        "beta_testers",
        tester["id"],
        {"feedback_count": int(tester.get("feedback_count") or 0) + 1},
    )

    return {"feedback_id": feedback["id"], "ticket_id": ticket["id"]}


@app.get("/beta/my-feedback")
def beta_my_feedback(
    auth: dict[str, str] = Depends(_beta_tester_auth),
) -> list[dict[str, Any]]:
    db = get_supabase()
    return db.select(
        "beta_feedback",
        filters={"tester_id": auth["tester_id"]},
        order_by="created_at",
        ascending=False,
        limit=50,
    )


@app.get("/beta/testers")
def beta_list_testers(project_id: str | None = None) -> list[dict[str, Any]]:
    db = get_supabase()
    filters = {"project_id": project_id} if project_id else None
    testers = db.select(
        "beta_testers",
        filters=filters,
        order_by="joined_at",
        ascending=False,
    )
    projects = {p["id"]: p["name"] for p in db.select("projects")}
    for tester in testers:
        tester["project_name"] = projects.get(tester.get("project_id"), "")
    return testers


@app.get("/beta/testers/export")
def beta_export_testers(project_id: str | None = None) -> StreamingResponse:
    testers = beta_list_testers(project_id=project_id)
    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow([
        "prénom", "email", "projet", "appareil", "os", "version_app",
        "feedbacks", "inscription",
    ])
    for t in testers:
        writer.writerow([
            t.get("first_name") or "",
            t.get("email") or "",
            t.get("project_name") or "",
            t.get("device") or "",
            t.get("os_version") or "",
            t.get("app_version") or "",
            t.get("feedback_count") or 0,
            t.get("joined_at") or "",
        ])
    buffer.seek(0)
    return StreamingResponse(
        iter([buffer.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": 'attachment; filename="beta_testers.csv"'},
    )


@app.get("/beta/feedback")
def beta_list_feedback(
    project_id: str | None = None,
    tester_id: str | None = None,
) -> list[dict[str, Any]]:
    db = get_supabase()
    filters: dict[str, Any] = {}
    if project_id:
        filters["project_id"] = project_id
    if tester_id:
        filters["tester_id"] = tester_id

    feedback = db.select(
        "beta_feedback",
        filters=filters or None,
        order_by="created_at",
        ascending=False,
        limit=200,
    )

    testers = {t["id"]: t for t in db.select("beta_testers")}
    projects = {p["id"]: p["name"] for p in db.select("projects")}
    for row in feedback:
        tester = testers.get(row.get("tester_id"), {})
        row["tester_name"] = tester.get("first_name")
        row["tester_email"] = tester.get("email")
        row["project_name"] = projects.get(row.get("project_id"), "")
    return feedback


@app.get("/beta/stats")
def beta_stats(project_id: str | None = None) -> dict[str, Any]:
    db = get_supabase()
    tester_filters = {"project_id": project_id} if project_id else None
    feedback_filters = {"project_id": project_id} if project_id else None

    testers = db.select("beta_testers", filters=tester_filters)
    feedback = db.select("beta_feedback", filters=feedback_filters)

    week_ago = datetime.now(timezone.utc) - timedelta(days=7)
    feedback_this_week = 0
    by_type: dict[str, int] = {}
    by_severity: dict[str, int] = {}
    timeline: dict[str, int] = {}

    for row in feedback:
        created = row.get("created_at")
        if created:
            try:
                dt = datetime.fromisoformat(created.replace("Z", "+00:00"))
                if dt >= week_ago:
                    feedback_this_week += 1
                day_key = dt.date().isoformat()
                timeline[day_key] = timeline.get(day_key, 0) + 1
            except ValueError:
                pass

        fb_type = row.get("type") or "autre"
        by_type[fb_type] = by_type.get(fb_type, 0) + 1
        sev = row.get("severity") or "non_renseigné"
        by_severity[sev] = by_severity.get(sev, 0) + 1

    # Last 7 days timeline (fill gaps)
    timeline_7d: list[dict[str, Any]] = []
    today = datetime.now(timezone.utc).date()
    for i in range(6, -1, -1):
        day = today - timedelta(days=i)
        key = day.isoformat()
        timeline_7d.append({"date": key, "count": timeline.get(key, 0)})

    return {
        "total_testers": len(testers),
        "total_feedback": len(feedback),
        "feedback_this_week": feedback_this_week,
        "by_type": by_type,
        "by_severity": by_severity,
        "timeline_7d": timeline_7d,
    }


@app.post("/beta/invite")
def beta_invite(body: BetaInviteRequest) -> dict[str, str]:
    db = get_supabase()
    rows = db.select("projects", filters={"id": body.project_id})
    if not rows:
        raise HTTPException(status_code=404, detail="Projet introuvable")
    slug = project_slug_for(rows[0])
    return {"invite_url": invite_url_for_slug(slug), "project_slug": slug}


# ---------------------------------------------------------------------------
# Waitlist — pre-launch email collection
# ---------------------------------------------------------------------------
@app.get("/waitlist/info/{project_slug}")
def waitlist_info(project_slug: str) -> dict[str, Any]:
    db = get_supabase()
    project = resolve_project_by_slug(db, project_slug)
    return {
        "project_id": project["id"],
        "project_name": project["name"],
        "project_slug": project_slug_for(project),
        "description": project.get("description") or "",
        "status": project.get("status"),
    }


@app.get("/waitlist/count/{project_slug}")
def waitlist_count(project_slug: str) -> dict[str, int]:
    db = get_supabase()
    project = resolve_project_by_slug(db, project_slug)
    rows = db.select("waitlist", filters={"project_id": project["id"]})
    return {"count": len(rows)}


@app.post("/waitlist/join")
def waitlist_join(body: WaitlistJoinRequest) -> dict[str, int]:
    db = get_supabase()
    project = resolve_project_by_slug(db, body.project_slug)
    email = body.email.strip().lower()

    existing = db.select(
        "waitlist",
        filters={"project_id": project["id"], "email": email},
    )
    if existing:
        entry = existing[0]
    else:
        entry = db.insert(
            "waitlist",
            {
                "project_id": project["id"],
                "email": email,
                "first_name": (body.first_name or "").strip() or None,
                "source": (body.source or "direct").strip() or "direct",
                "message": (body.message or "").strip() or None,
                "status": "waiting",
            },
        )

    position, total = compute_position(db, project["id"], entry["id"])
    return {"position": position, "total": total}


@app.get("/waitlist")
def waitlist_list(
    project_id: str | None = None,
    status: str | None = None,
    source: str | None = None,
) -> list[dict[str, Any]]:
    db = get_supabase()
    filters: dict[str, Any] = {}
    if project_id:
        filters["project_id"] = project_id
    if status:
        filters["status"] = status
    if source:
        filters["source"] = source

    rows = db.select(
        "waitlist",
        filters=filters or None,
        order_by="created_at",
        ascending=False,
    )
    projects = {p["id"]: p["name"] for p in db.select("projects")}
    for row in rows:
        row["project_name"] = projects.get(row.get("project_id"), "")
    return rows


@app.get("/waitlist/stats")
def waitlist_stats_endpoint(project_id: str | None = None) -> dict[str, Any]:
    db = get_supabase()
    return waitlist_stats(db, project_id=project_id)


@app.post("/waitlist/notify")
def waitlist_notify(body: WaitlistNotifyRequest) -> dict[str, Any]:
    db = get_supabase()
    filters: dict[str, Any] = {"project_id": body.project_id}
    if body.status_filter:
        filters["status"] = body.status_filter
    else:
        filters["status"] = "waiting"

    rows = db.select("waitlist", filters=filters)
    now = datetime.now(timezone.utc).isoformat()
    notified_count = 0

    for row in rows:
        db.update(
            "waitlist",
            row["id"],
            {"status": "notified", "notified_at": now},
        )
        notified_count += 1

    preview_html = markdown_to_html(body.message_md, subject=body.subject)
    return {"notified_count": notified_count, "preview_html": preview_html}


@app.post("/waitlist/generate-email")
def waitlist_generate_email(body: WaitlistGenerateEmailRequest) -> dict[str, str]:
    db = get_supabase()
    try:
        return generate_waitlist_email(db, body.project_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except Exception as exc:
        logger.exception("waitlist_generate_email failed")
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.patch("/waitlist/{entry_id}")
def waitlist_update_status(entry_id: str, body: WaitlistStatusUpdate) -> dict[str, Any]:
    db = get_supabase()
    rows = db.select("waitlist", filters={"id": entry_id})
    if not rows:
        raise HTTPException(status_code=404, detail="Inscription introuvable")
    values: dict[str, Any] = {"status": body.status}
    if body.status == "notified":
        values["notified_at"] = datetime.now(timezone.utc).isoformat()
    return db.update("waitlist", entry_id, values)


@app.delete("/waitlist/{entry_id}")
def waitlist_delete(entry_id: str) -> dict[str, bool]:
    db = get_supabase()
    rows = db.select("waitlist", filters={"id": entry_id})
    if not rows:
        raise HTTPException(status_code=404, detail="Inscription introuvable")
    db.delete("waitlist", entry_id)
    return {"ok": True}


@app.get("/waitlist/export/{project_id}")
def waitlist_export(project_id: str) -> StreamingResponse:
    db = get_supabase()
    rows = db.select(
        "waitlist",
        filters={"project_id": project_id},
        order_by="created_at",
        ascending=True,
    )
    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(["email", "prénom", "source", "date"])
    for row in rows:
        writer.writerow([
            row.get("email") or "",
            row.get("first_name") or "",
            row.get("source") or "",
            row.get("created_at") or "",
        ])
    buffer.seek(0)
    return StreamingResponse(
        iter([buffer.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": 'attachment; filename="waitlist.csv"'},
    )


@app.get("/waitlist/page-url/{project_id}")
def waitlist_page_url(project_id: str) -> dict[str, str]:
    db = get_supabase()
    rows = db.select("projects", filters={"id": project_id})
    if not rows:
        raise HTTPException(status_code=404, detail="Projet introuvable")
    slug = project_slug_for(rows[0])
    return {"page_url": waitlist_url_for_slug(slug), "project_slug": slug}


# ---------------------------------------------------------------------------
# === PARTNERSHIPS ===
# ---------------------------------------------------------------------------
def _partner_row_to_api(row: dict[str, Any]) -> dict[str, Any]:
    return {
        **row,
        "project_ids": row.get("project_ids") or [],
    }


def _serialize_partner_dates(values: dict[str, Any]) -> dict[str, Any]:
    out = dict(values)
    for key in ("next_followup", "last_contact_date"):
        if key in out and out[key] is not None and hasattr(out[key], "isoformat"):
            out[key] = out[key].isoformat()
    return out


@app.get("/partners")
def list_partners(
    type: str | None = None,
    status: str | None = None,
    direction: str | None = None,
    project_id: str | None = None,
) -> list[dict[str, Any]]:
    db = get_supabase()
    filters: dict[str, Any] = {}
    if type:
        filters["type"] = type
    if status:
        filters["status"] = status
    if direction:
        filters["direction"] = direction
    rows = db.select(
        "partners",
        filters=filters or None,
        order_by="updated_at",
        ascending=False,
    )
    if project_id:
        rows = [r for r in rows if project_id in (r.get("project_ids") or [])]
    return [_partner_row_to_api(r) for r in rows]


@app.post("/partners")
def create_partner(body: PartnerCreate) -> dict[str, Any]:
    db = get_supabase()
    row = db.insert(
        "partners",
        _serialize_partner_dates(
            {
                "type": body.type,
                "direction": body.direction,
                "name": body.name,
                "status": body.status,
                "company": body.company,
                "email": body.email,
                "instagram_url": body.instagram_url,
                "tiktok_url": body.tiktok_url,
                "youtube_url": body.youtube_url,
                "website": body.website,
                "audience_size": body.audience_size,
                "audience_description": body.audience_description,
                "project_ids": body.project_ids or [],
                "notes": body.notes or "",
                "next_followup": body.next_followup,
                "last_contact_date": body.last_contact_date,
            }
        ),
    )
    return _partner_row_to_api(row)


@app.patch("/partners/{partner_id}")
def update_partner(partner_id: str, body: PartnerUpdate) -> dict[str, Any]:
    db = get_supabase()
    rows = db.select("partners", filters={"id": partner_id})
    if not rows:
        raise HTTPException(status_code=404, detail="Partenaire introuvable")
    values = body.model_dump(exclude_none=True)
    if not values:
        raise HTTPException(status_code=400, detail="Aucun champ à mettre à jour")
    updated = db.update("partners", partner_id, _serialize_partner_dates(values))
    return _partner_row_to_api(updated)


@app.get("/partners/stats")
def partners_stats() -> dict[str, Any]:
    return partnership_stats(get_supabase())


@app.delete("/partners/{partner_id}")
def delete_partner(partner_id: str) -> dict[str, str]:
    db = get_supabase()
    rows = db.select("partners", filters={"id": partner_id})
    if not rows:
        raise HTTPException(status_code=404, detail="Partenaire introuvable")
    db.delete("partners", partner_id)
    return {"status": "deleted", "id": partner_id}


@app.get("/partners/{partner_id}/interactions")
def list_partner_interactions(partner_id: str) -> list[dict[str, Any]]:
    db = get_supabase()
    if not db.select("partners", filters={"id": partner_id}):
        raise HTTPException(status_code=404, detail="Partenaire introuvable")
    return db.select(
        "partner_interactions",
        filters={"partner_id": partner_id},
        order_by="date",
        ascending=False,
    )


@app.post("/partners/{partner_id}/interactions")
def create_partner_interaction(
    partner_id: str,
    body: PartnerInteractionCreate,
) -> dict[str, Any]:
    db = get_supabase()
    partner_rows = db.select("partners", filters={"id": partner_id})
    if not partner_rows:
        raise HTTPException(status_code=404, detail="Partenaire introuvable")
    payload: dict[str, Any] = {
        "partner_id": partner_id,
        "type": body.type,
        "note": body.note or "",
    }
    if body.date:
        payload["date"] = body.date.isoformat()
    row = db.insert("partner_interactions", payload)
    db.update(
        "partners",
        partner_id,
        {"last_contact_date": date.today().isoformat()},
    )
    return row


@app.get("/partners/{partner_id}/contract")
def get_partner_contract(partner_id: str) -> dict[str, str | None]:
    db = get_supabase()
    rows = db.select("partners", filters={"id": partner_id})
    if not rows:
        raise HTTPException(status_code=404, detail="Partenaire introuvable")
    return {"contract_path": rows[0].get("contract_path")}


@app.post("/partners/{partner_id}/contract")
async def upload_partner_contract(
    partner_id: str,
    file: UploadFile = File(...),
) -> dict[str, Any]:
    db = get_supabase()
    rows = db.select("partners", filters={"id": partner_id})
    if not rows:
        raise HTTPException(status_code=404, detail="Partenaire introuvable")
    partner = rows[0]
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Fichier PDF requis")

    dest = build_contract_path(partner["name"], partner["type"])
    dest.parent.mkdir(parents=True, exist_ok=True)
    content = await file.read()
    dest.write_bytes(content)

    updated = db.update(
        "partners",
        partner_id,
        {"contract_path": str(dest)},
    )
    return _partner_row_to_api(updated)


@app.get("/partners/{partner_id}/contract/open")
def open_partner_contract(partner_id: str) -> dict[str, bool]:
    db = get_supabase()
    rows = db.select("partners", filters={"id": partner_id})
    if not rows:
        raise HTTPException(status_code=404, detail="Partenaire introuvable")
    path = rows[0].get("contract_path")
    if not path:
        raise HTTPException(status_code=404, detail="Aucun contrat enregistré")
    try:
        open_contract_file(path)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except OSError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    return {"ok": True}


@app.post("/partners/contracts/open-folder")
def open_contracts_folder_endpoint() -> dict[str, bool]:
    try:
        open_contracts_folder()
    except OSError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    return {"ok": True, "path": str(CONTRACTS_ROOT)}


@app.get("/affiliate-links")
def list_affiliate_links(partner_id: str | None = None) -> list[dict[str, Any]]:
    db = get_supabase()
    filters = {"partner_id": partner_id} if partner_id else None
    return db.select(
        "affiliate_links",
        filters=filters,
        order_by="created_at",
        ascending=False,
    )


@app.post("/affiliate-links")
def create_affiliate_link(body: AffiliateLinkCreate) -> dict[str, Any]:
    db = get_supabase()
    if not db.select("partners", filters={"id": body.partner_id}):
        raise HTTPException(status_code=404, detail="Partenaire introuvable")

    code = (body.code or "").strip().upper() or generate_affiliate_code()
    for _ in range(5):
        existing = db.select("affiliate_links", filters={"code": code})
        if not existing:
            break
        code = generate_affiliate_code()

    row = db.insert(
        "affiliate_links",
        {
            "partner_id": body.partner_id,
            "project_id": body.project_id,
            "code": code,
            "redirect_url": body.redirect_url,
            "commission_type": body.commission_type,
            "commission_value": body.commission_value,
            "active": body.active,
        },
    )
    settings = get_settings()
    base = settings.beta_portal_base_url.replace(":3000", ":8000")
    if "localhost" in base:
        base = f"http://localhost:{settings.api_port}"
    row["public_url"] = affiliate_public_url(code, base)
    return row


@app.patch("/affiliate-links/{link_id}")
def update_affiliate_link(link_id: str, body: AffiliateLinkUpdate) -> dict[str, Any]:
    db = get_supabase()
    rows = db.select("affiliate_links", filters={"id": link_id})
    if not rows:
        raise HTTPException(status_code=404, detail="Lien affilié introuvable")
    values = body.model_dump(exclude_none=True)
    if not values:
        raise HTTPException(status_code=400, detail="Aucun champ à mettre à jour")
    return db.update("affiliate_links", link_id, values)


@app.get("/affiliate-links/{link_id}/timeline")
def affiliate_link_timeline_endpoint(
    link_id: str,
    days: int = Query(default=30, ge=1, le=90),
) -> list[dict[str, Any]]:
    db = get_supabase()
    if not db.select("affiliate_links", filters={"id": link_id}):
        raise HTTPException(status_code=404, detail="Lien affilié introuvable")
    return affiliate_link_timeline(db, link_id, days)


@app.get("/go/{code}")
def affiliate_redirect(
    code: str,
    user_agent: str | None = Header(default=None, alias="User-Agent"),
    referer: str | None = Header(default=None, alias="Referer"),
):
    db = get_supabase()
    rows = db.select("affiliate_links", filters={"code": code.upper()})
    if not rows or not rows[0].get("active"):
        return RedirectResponse(url=AFFILIATE_FALLBACK_URL, status_code=302)
    link = rows[0]
    try:
        record_affiliate_click(db, link, user_agent, referer)
    except Exception:
        logger.exception("Affiliate click logging failed for code=%s", code)
    return RedirectResponse(url=link["redirect_url"], status_code=302)


@app.post("/go/{code}/conversion")
def affiliate_conversion(code: str, body: AffiliateConversionBody) -> dict[str, Any]:
    db = get_supabase()
    rows = db.select("affiliate_links", filters={"code": code.upper()})
    if not rows:
        raise HTTPException(status_code=404, detail="Lien affilié introuvable")
    return record_affiliate_conversion(db, rows[0], body.revenue)


@app.post("/partnerships/request")
def create_partnership_request(body: PartnershipRequestCreate) -> dict[str, Any]:
    db = get_supabase()
    return db.insert(
        "partnership_requests",
        body.model_dump(),
    )


@app.get("/partnerships/requests")
def list_partnership_requests(
    status: str | None = None,
) -> list[dict[str, Any]]:
    db = get_supabase()
    filters = {"status": status} if status else None
    return db.select(
        "partnership_requests",
        filters=filters,
        order_by="created_at",
        ascending=False,
    )


@app.patch("/partnerships/requests/{request_id}")
def update_partnership_request(
    request_id: str,
    body: PartnershipRequestUpdate,
) -> dict[str, Any]:
    db = get_supabase()
    rows = db.select("partnership_requests", filters={"id": request_id})
    if not rows:
        raise HTTPException(status_code=404, detail="Demande introuvable")
    values = body.model_dump(exclude_none=True)
    if not values:
        raise HTTPException(status_code=400, detail="Aucun champ à mettre à jour")
    return db.update("partnership_requests", request_id, values)


@app.post("/partnerships/requests/{request_id}/convert")
def convert_partnership_request(request_id: str) -> dict[str, Any]:
    db = get_supabase()
    req_rows = db.select("partnership_requests", filters={"id": request_id})
    if not req_rows:
        raise HTTPException(status_code=404, detail="Demande introuvable")
    req = req_rows[0]

    partner_type = req.get("type") or "other"
    if partner_type == "other":
        partner_type = "creator"

    audience = parse_audience_size_text(req.get("audience_size"))

    partner = db.insert(
        "partners",
        {
            "type": partner_type,
            "direction": "inbound",
            "name": req["name"],
            "email": req.get("email"),
            "instagram_url": req.get("instagram_url"),
            "tiktok_url": req.get("tiktok_url"),
            "website": req.get("website"),
            "audience_size": audience,
            "audience_description": req.get("audience_size"),
            "notes": req.get("message") or "",
            "status": "prospect",
        },
    )

    db.update(
        "partnership_requests",
        request_id,
        {"status": "converted", "partner_id": partner["id"]},
    )
    return {
        "partner": _partner_row_to_api(partner),
        "request_id": request_id,
    }


# ---------------------------------------------------------------------------
# Finances
# ---------------------------------------------------------------------------
def _finance_tx_row(body: FinanceTransactionCreate) -> dict[str, Any]:
    return {
        "date": body.tx_date.isoformat(),
        "type": body.type,
        "amount": body.amount,
        "currency": body.currency,
        "category": body.category,
        "project_id": body.project_id,
        "description": body.description,
        "is_recurring": body.is_recurring,
        "recurrence": body.recurrence if body.is_recurring else None,
    }


@app.get("/finances/transactions")
def list_finance_transactions(
    month: str | None = Query(default=None, pattern=r"^\d{4}-\d{2}$"),
    type: str | None = Query(default=None, pattern="^(income|expense)$"),
    category: str | None = None,
    project_id: str | None = None,
) -> list[dict[str, Any]]:
    db = get_supabase()
    rows = fetch_finance_transactions(
        db,
        month=month,
        tx_type=type,
        category=category,
        project_id=project_id,
    )
    return attach_project_names(db, rows)


@app.post("/finances/transactions")
def create_finance_transaction(body: FinanceTransactionCreate) -> dict[str, Any]:
    db = get_supabase()
    return db.insert("transactions", _finance_tx_row(body))


@app.patch("/finances/transactions/{transaction_id}")
def update_finance_transaction(
    transaction_id: str,
    body: FinanceTransactionUpdate,
) -> dict[str, Any]:
    db = get_supabase()
    rows = db.select("transactions", filters={"id": transaction_id})
    if not rows:
        raise HTTPException(status_code=404, detail="Transaction introuvable")

    updates = body.model_dump(exclude_unset=True, by_alias=True)
    if "date" in updates and updates["date"] is not None:
        updates["date"] = updates["date"].isoformat()
    if updates.get("is_recurring") is False:
        updates["recurrence"] = None
    if not updates:
        return rows[0]
    return db.update("transactions", transaction_id, updates)


@app.delete("/finances/transactions/{transaction_id}")
def delete_finance_transaction(transaction_id: str) -> dict[str, bool]:
    db = get_supabase()
    rows = db.select("transactions", filters={"id": transaction_id})
    if not rows:
        raise HTTPException(status_code=404, detail="Transaction introuvable")
    db.delete("transactions", transaction_id)
    return {"ok": True}


@app.get("/finances/summary/{month}")
def get_finance_summary(month: str) -> dict[str, Any]:
    try:
        return get_or_generate_summary(month)
    except Exception as exc:
        logger.exception("Finance summary failed for %s", month)
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.post("/finances/summary/generate")
def regenerate_finance_summary(body: FinanceSummaryGenerate) -> dict[str, Any]:
    try:
        return generate_monthly_summary(body.month, force=True)
    except Exception as exc:
        logger.exception("Finance summary regeneration failed for %s", body.month)
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.get("/finances/dashboard")
def finance_dashboard(
    month: str | None = Query(default=None, pattern=r"^\d{4}-\d{2}$"),
) -> dict[str, Any]:
    db = get_supabase()
    data = build_dashboard(db, month=month)
    data["recurring_expenses"] = attach_project_names(
        db, data["recurring_expenses"]
    )
    return data


# ---------------------------------------------------------------------------
# Composio OAuth Gateway
# ---------------------------------------------------------------------------
@app.get("/composio/apps")
async def list_composio_apps(user_id: str = "alnua_coo"):
    """Liste les apps connectées via Composio OAuth."""
    from skills.skill_composio import list_connected_apps

    return list_connected_apps(user_id=user_id)


@app.post("/composio/connect/{app_name}")
async def connect_composio_app(app_name: str, user_id: str = "alnua_coo"):
    """Génère un lien OAuth pour connecter une app. Renvoie le lien à ouvrir."""
    from skills.skill_composio import get_oauth_link

    link = get_oauth_link(app=app_name.upper(), user_id=user_id)
    return {"app": app_name, "oauth_url": link}


# ---------------------------------------------------------------------------
# CLI entry
# ---------------------------------------------------------------------------
def main() -> None:
    import uvicorn
    settings = get_settings()
    logging.basicConfig(level=logging.INFO)
    uvicorn.run(
        "api.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=False,
    )


if __name__ == "__main__":
    main()
