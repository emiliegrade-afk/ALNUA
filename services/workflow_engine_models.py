"""Workflow engine — Pydantic models and shared types."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Literal

from pydantic import BaseModel, Field

StepStatus = Literal["PENDING", "IN_PROGRESS", "OK", "A_VERIFIER", "ECART", "RETRYABLE"]
RunStatus = Literal["running", "completed", "blocked", "failed", "cancelled"]


class WorkflowStepDef(BaseModel):
    id: str
    label: str
    head_agent: str = "coo"


class WorkflowRecipe(BaseModel):
    id: str
    name: str
    description: str
    head_agent: str
    steps: list[WorkflowStepDef]
    priority: str = "P0"


class StepRun(BaseModel):
    step_id: str
    label: str
    status: StepStatus = "PENDING"
    detail: str = ""
    gaps: list[str] = Field(default_factory=list)
    started_at: str | None = None
    finished_at: str | None = None
    result: dict[str, Any] | None = None


class WorkflowRun(BaseModel):
    run_id: str
    recipe_id: str
    context: dict[str, Any] = Field(default_factory=dict)
    status: RunStatus = "running"
    steps: list[StepRun] = Field(default_factory=list)
    blocked_at_step: str | None = None
    created_at: str = Field(default_factory=lambda: _now_iso())
    finished_at: str | None = None
    summary: str = ""


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()
