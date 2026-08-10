"""Models and shared constants for App Factory (Phase 2)."""

from __future__ import annotations

import re
import uuid
from datetime import datetime, timezone
from typing import Any, Literal

from pydantic import BaseModel, Field

from config.paths import get_hub_repo_path
from services.coding_pipeline import DevStack

_FACTORY_STACK = Literal["nextjs", "expo"]
_RUNS: dict[str, dict[str, Any]] = {}
_PLANS_DIR = get_hub_repo_path() / "data" / "app_factory"

GITHUB_API = "https://api.github.com"


class FactoryTask(BaseModel):
    title: str
    description: str
    files_to_create: list[str] = Field(default_factory=list)
    files_to_modify: list[str] = Field(default_factory=list)
    tests_to_pass: list[str] = Field(default_factory=list)
    priority: str = "P0"


class AppFactoryRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=120)
    brief: str = Field(..., min_length=10, max_length=8000)
    stack: _FACTORY_STACK = "nextjs"
    slug: str = ""
    github_repo: str = ""
    local_path: str = ""
    branch: Literal["app", "gaming", "robotics", "other"] = "app"
    auto_run_pipeline: bool = True


def slugify(value: str) -> str:
    s = re.sub(r"[^a-z0-9]+", "-", value.strip().lower()).strip("-")
    return s or "app"


def default_local_path(slug: str) -> str:
    parent = get_hub_repo_path().parent
    return str(parent / slug)


def stack_value(stack: _FACTORY_STACK) -> str:
    return DevStack.NEXTJS.value if stack == "nextjs" else DevStack.REACT_NATIVE_EXPO.value


def new_run_id() -> str:
    return str(uuid.uuid4())


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()
