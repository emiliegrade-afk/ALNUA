"""Pydantic models — split from schemas.py (debt paydown)."""

from __future__ import annotations

from datetime import date, datetime

from pydantic import BaseModel, Field

class DevLogCreate(BaseModel):
    project_id: str
    content: str
    log_date: date | None = None


class TicketCreate(BaseModel):
    project_id: str
    type: str = Field(pattern="^(bug|feature|improvement|crash)$")
    priority: str = Field(default="medium", pattern="^(critical|high|medium|low)$")
    title: str = Field(min_length=1)
    description: str = ""
    source: str = Field(
        default="emilie",
        pattern="^(qa_agent|sav_bot|reviews_bot|emilie|quick_capture|beta_tester|partnerships_bot)$",
    )
    assignee_agent_id: str | None = None
    story_points: int | None = Field(default=None, ge=1, le=21)
    due_date: date | None = None


class TicketUpdate(BaseModel):
    status: str | None = Field(
        default=None,
        pattern="^(open|in_progress|in_review|done|wont_fix)$",
    )
    title: str | None = None
    description: str | None = None
    priority: str | None = Field(
        default=None,
        pattern="^(critical|high|medium|low)$",
    )
    cursor_prompt: str | None = None
    assignee_agent_id: str | None = None
    story_points: int | None = Field(default=None, ge=1, le=21)
    due_date: date | None = None


class GamingBuildCreate(BaseModel):
    project_id: str
    branch: str = Field(min_length=1)
    build_number: str = Field(min_length=1)
    game_version: str | None = None
    engine_version: str = "5.8"
    status: str = Field(default="success", pattern="^(success|failed|running)$")
    fps_avg: float | None = None
    crashes: int | None = Field(default=None, ge=0)
    draw_calls: int | None = Field(default=None, ge=0)
    commit_sha: str | None = None
    notes: str = ""


class GamingAssetEntry(BaseModel):
    category: str = Field(min_length=1)
    name: str = Field(min_length=1)
    asset_type: str = Field(min_length=1)
    file_path: str = Field(min_length=1)
    size_bytes: int = Field(default=0, ge=0)
    modified_at: datetime | None = None


class GamingAssetsSync(BaseModel):
    project_id: str
    assets: list[GamingAssetEntry]


class RoboBuildCreate(BaseModel):
    project_id: str
    branch: str = Field(min_length=1)
    stage: str = Field(default="Prototype", pattern="^(Prototype|V2|V3|Certification|Production)$")
    version: str | None = None
    pcb_revision: str | None = None
    firmware_version: str | None = None
    tests_passed_pct: int | None = Field(default=None, ge=0, le=100)
    open_issues: int | None = Field(default=None, ge=0)
    notes: str = ""


class RoboLabTestCreate(BaseModel):
    project_id: str
    category: str = Field(min_length=1)
    name: str = Field(min_length=1)
    status: str = Field(default="in_progress", pattern="^(pass|fail|in_progress)$")
    measured_value: str | None = None
    notes: str = ""


class RoboTelemetryCreate(BaseModel):
    project_id: str
    power_w: float | None = None
    temperature_c: float | None = None
    cpu_pct: int | None = Field(default=None, ge=0, le=100)
    battery_pct: int | None = Field(default=None, ge=0, le=100)
    charge_cycles: int | None = Field(default=None, ge=0)
    autonomy_hours: float | None = None


class ModuleCreate(BaseModel):
    project_id: str
    name: str = Field(min_length=1)
    status: str = Field(default="a_faire", pattern="^(a_faire|en_developpement|en_test|termine)$")
    progress: int = Field(default=0, ge=0, le=100)
    features_done: int = Field(default=0, ge=0)
    features_total: int = Field(default=0, ge=0)
    tests_passed_pct: int = Field(default=0, ge=0, le=100)
    open_bugs: int = Field(default=0, ge=0)


class ModuleUpdate(BaseModel):
    name: str | None = None
    status: str | None = Field(default=None, pattern="^(a_faire|en_developpement|en_test|termine)$")
    progress: int | None = Field(default=None, ge=0, le=100)
    features_done: int | None = Field(default=None, ge=0)
    features_total: int | None = Field(default=None, ge=0)
    tests_passed_pct: int | None = Field(default=None, ge=0, le=100)
    open_bugs: int | None = Field(default=None, ge=0)


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
    project_id: str = Field(min_length=1)
    priority: str | None = Field(
        default="medium",
        pattern="^(critical|high|medium|low)$",
    )
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


