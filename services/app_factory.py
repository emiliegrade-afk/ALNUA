"""App factory — brief → MVP plan → GitHub issues → coding pipeline (Phase 2)."""

from __future__ import annotations

from services.app_factory_issues import create_issue_on_repo, format_issue_body  # noqa: F401 — re-export
from services.app_factory_models import (  # noqa: F401 — re-export
    AppFactoryRequest,
    FactoryTask,
    GITHUB_API,
    _PLANS_DIR,
    _RUNS,
)
from services.app_factory_plan import (  # noqa: F401 — re-export
    fallback_plan as _fallback_plan,
    generate_factory_plan,
)
from services.app_factory_run import (  # noqa: F401 — re-export
    get_factory_run,
    list_factory_runs,
    run_app_factory_sync,
    start_app_factory_run,
    trigger_pipeline_for_run,
)
from services.app_factory_scaffold import ensure_local_scaffold, register_factory_app  # noqa: F401 — re-export
from services.app_factory_models import slugify as _slugify  # noqa: F401 — re-export

__all__ = [
    "AppFactoryRequest",
    "FactoryTask",
    "GITHUB_API",
    "_PLANS_DIR",
    "_RUNS",
    "_fallback_plan",
    "_slugify",
    "create_issue_on_repo",
    "ensure_local_scaffold",
    "format_issue_body",
    "generate_factory_plan",
    "get_factory_run",
    "list_factory_runs",
    "register_factory_app",
    "run_app_factory_sync",
    "start_app_factory_run",
    "trigger_pipeline_for_run",
]
