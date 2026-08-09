"""Pydantic models — split from schemas.py (debt paydown)."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

class OrchestrationMorningRequest(BaseModel):
    weekly_plan: bool = False


class OrchestrationSpecQaRequest(BaseModel):
    spec_text: str = Field(min_length=10)
    context: str = ""
    rounds: int = Field(default=2, ge=1, le=3)
    stop_on_approve: bool = True
    create_qa_ticket: bool = True
    project_id: str | None = None
    project_slug: str | None = None
    ticket_title: str | None = None


class OrchestrationGithubPrRequest(BaseModel):
    repo: str = Field(min_length=1)
    pr_number: int = Field(ge=1)
    title: str = ""
    diff_summary: str = ""
    changed_files: str = ""


class OrchestrationWelcomeRequest(BaseModel):
    recipient_name: str = Field(min_length=1)
    recipient_email: str = Field(min_length=3)
    project: str = "ALNUA"
    language: str = "fr"


class OrchestrationContentSprintRequest(BaseModel):
    brief: str = Field(min_length=5)
    platforms: list[str] | None = None
    project: str = "ALNUA"


class AcademySeedRequest(BaseModel):
    level: int = Field(ge=1, le=4, description="Niveau curriculum 1-4")
    dry_run: bool = False
    mark_first_ready: bool = False


class AcademySprintRequest(BaseModel):
    level: int | None = Field(default=None, ge=1, le=4)
    seed_if_missing: bool = True
    mark_ready_count: int = Field(default=3, ge=1, le=10)


class AcademyPollRequest(BaseModel):
    mark_ready_if_idle: bool = True
    mark_ready_count: int = Field(default=2, ge=0, le=10)
    notify: bool = False


class WakeAgentsRequest(BaseModel):
    """CEO kick — retry failed + queue next Academy issues."""

    retry_failed: bool = True
    mark_ready_count: int | None = Field(default=None, ge=1, le=10)
    sync: bool = True
    notify: bool = False


class AcademyHumanLessonRequest(BaseModel):
    """CEO manual fix → agents learn via journal + Mem0."""

    cause: str = Field(min_length=5, max_length=2000)
    fix: str = Field(min_length=5, max_length=2000)
    files: list[str] = Field(default_factory=list)
    issue_number: int | None = Field(default=None, ge=1)
    repo_slug: str = Field(default="academy", max_length=64)
    agent_id: str = Field(default="dev_app", max_length=64)


class EngineeringSpecGenerateRequest(BaseModel):
    force: bool = False
    debate_rounds: int = Field(default=1, ge=0, le=3)
    refine_with_pm: bool = True


class PrdDecomposeRequest(BaseModel):
    repo_slug: str | None = Field(
        default=None,
        description="hub | registry slug — auto si omis",
    )
    dry_run: bool = False
    mark_ready_count: int = Field(default=3, ge=0, le=20)
    force_spec: bool = False
    debate_rounds: int = Field(default=1, ge=0, le=3)


class PrdDecomposeOrchestrationRequest(BaseModel):
    dossier_id: str = Field(min_length=8)
    repo_slug: str | None = None
    dry_run: bool = False
    mark_ready_count: int = Field(default=3, ge=0, le=20)
    force_spec: bool = False


class SentrySimulateRequest(BaseModel):
    title: str = Field(min_length=3, max_length=200)
    message: str = ""
    project_slug: str = "hub"
    level: str = "error"
    dry_run: bool = False


# ---------------------------------------------------------------------------
# Tier 2 Services — Trend Monitor, Deep Research, Plan Executor, Code Graph
# ---------------------------------------------------------------------------

class TrendBriefRequest(BaseModel):
    topics: list[str] = Field(min_length=1, description="Thèmes à surveiller")
    sources: list[str] = Field(
        default_factory=lambda: ["hackernews", "reddit", "github"],
        description="Sources : hackernews | reddit | github",
    )
    agent_id: str = Field(default="marketing", description="Agent qui synthétise")
    limit: int = Field(default=20, ge=5, le=50)


class TrendRawRequest(BaseModel):
    sources: list[str] = Field(
        default_factory=lambda: ["hackernews", "reddit", "github"],
    )
    topics: list[str] = Field(default_factory=list)
    limit: int = Field(default=30, ge=5, le=100)


class DeepResearchRequest(BaseModel):
    query: str = Field(min_length=5, description="Question ou sujet à rechercher")
    context: str = Field(default="", description="Contexte supplémentaire")
    rounds: int = Field(default=3, ge=1, le=3, description="Nombre de rounds (1-3)")
    agent_id: str = Field(
        default="brainstorm",
        description="Agent : brainstorm | rnd_agent | analyst_business",
    )


class QuickResearchRequest(BaseModel):
    query: str = Field(min_length=5)
    context: str = ""
    agent_id: str = "brainstorm"


class PlanStepRequest(BaseModel):
    step_id: str
    description: str
    agent_id: str
    method: str
    kwargs: dict[str, Any] = Field(default_factory=dict)
    depends_on: list[str] = Field(default_factory=list)


class PlanExecuteRequest(BaseModel):
    title: str
    steps: list[PlanStepRequest]
    context: str = ""
    max_concurrent: int = Field(default=4, ge=1, le=5)
    stop_on_failure: bool = False


class CooRunRequest(BaseModel):
    objective: str = Field(min_length=5, description="Objectif à atteindre")
    context: str = Field(default="", description="Contexte supplémentaire")
    max_concurrent: int = Field(default=4, ge=1, le=5)
    stop_on_failure: bool = False


class CodeGraphQueryRequest(BaseModel):
    question: str = Field(min_length=5, description="Question sur le codebase")
    agent_id: str = Field(default="analyst_data")
    rebuild: bool = Field(default=False, description="Forcer le rebuild du graphe")


class MemoryCompressRequest(BaseModel):
    agent_id: str
    threshold: int = Field(default=20, ge=5)


class LibraryResearchRequest(BaseModel):
    """CEO research — archive everything in bureau library."""

    query: str = Field(min_length=3, max_length=500)
    bureaus: list[str] | None = Field(
        default=None,
        description="Optional bureau ids to prioritize (hub, app, rd, …)",
    )
    requested_by: str = Field(default="ceo", max_length=64)
    wait: bool = Field(
        default=False,
        description="Block until research completes (UI sync mode)",
    )


class LibraryReportRequest(BaseModel):
    days: int = Field(default=7, ge=1, le=90)


class LibraryEnrichRequest(BaseModel):
    """Push library entries into Mem0 for all bureau agents (Phase 3)."""

    days: int = Field(default=30, ge=1, le=180)
    timing: str | None = Field(
        default=None,
        description="Optional filter: now | later",
    )
    limit: int = Field(default=25, ge=1, le=100)


class LibraryDistributeAllRequest(BaseModel):
    """Distribute every library entry to bureau agents (background job)."""

    skip_distributed: bool = Field(
        default=True,
        description="Skip entry×agent pairs already in the distribution ledger",
    )
    timing: str | None = Field(
        default=None,
        description="Optional filter: now | later",
    )
    run_learning: bool = Field(
        default=False,
        description="Chain learn job after distribute (heavy — off by default)",
    )


class LibraryRetentionApplyRequest(BaseModel):
    compress: bool = True
    purge: bool = True
    dry_run: bool = False


class LibraryTopicLearnRequest(BaseModel):
    """Deep-learn a library topic into an agent's Mem0 + vault memory note."""

    agent_id: str = Field(min_length=1, max_length=64)
    force_digest: bool = Field(
        default=False,
        description="Rebuild topic digest even if cached in vault",
    )
    promote: bool = Field(
        default=True,
        description="Promote to knowledge skill when thresholds met",
    )


class LibraryVaultSyncRequest(BaseModel):
    """Re-export bureau library → Obsidian vault + rebuild topic catalog."""

    index_chroma: bool = Field(
        default=False,
        description="Also index library/*.md into Chroma collection alnua_library",
    )
    limit: int | None = Field(
        default=None,
        ge=1,
        description="Optional cap on entries exported (tests / dry runs)",
    )


class NomenclatureNextRequest(BaseModel):
    kind: str = Field(description="APP | GDD | LORE | ASSET | BUG | COLLAB | RND")
    slug: str | None = None
    scope: str | None = Field(default=None, description="WYR | NWA for lore/gdd/asset")
    subtype: str | None = Field(default=None, description="ENV | CHAR | VFX | MAT | SFX for assets")
    feature: bool = Field(default=False, description="APP feature ref (F00n)")
    create_note: bool = Field(default=False, description="Create Obsidian stub in vault")
    title: str | None = None


class NomenclatureValidateRequest(BaseModel):
    ref: str


