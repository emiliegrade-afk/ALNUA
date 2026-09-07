"""ALNUA Workflow Engine — Hermes-lite recipe runner with ECART blocking."""

from __future__ import annotations

from config.paths import get_hub_repo_path

_RUNS_DIR = get_hub_repo_path() / "data" / "workflow_runs"

from services.workflow_engine_catalog import (  # noqa: F401 — re-export  # noqa: E402
    RECIPE_CATALOG,
    get_recipe,
    list_recipes,
)
from services.workflow_engine_handlers import (  # noqa: F401 — re-export
    _STEP_HANDLERS,
    register_extension_recipes as _register_extension_recipes,
)
from services.workflow_engine_models import (  # noqa: F401 — re-export
    RunStatus,
    StepRun,
    StepStatus,
    WorkflowRecipe,
    WorkflowRun,
    WorkflowStepDef,
)
from services.workflow_engine_continue import (  # noqa: F401 — re-export
    approve_workflow_step,
    continue_workflow_run,
    reject_workflow_step,
)
from services.workflow_engine_run import abort_workflow_run, run_workflow  # noqa: F401 — re-export
from services.workflow_engine_store import get_run, list_runs, save_run  # noqa: F401 — re-export

__all__ = [
    "_RUNS_DIR",
    "RECIPE_CATALOG",
    "RunStatus",
    "StepRun",
    "StepStatus",
    "WorkflowRecipe",
    "WorkflowRun",
    "WorkflowStepDef",
    "_STEP_HANDLERS",
    "abort_workflow_run",
    "approve_workflow_step",
    "continue_workflow_run",
    "reject_workflow_step",
    "get_recipe",
    "get_run",
    "list_recipes",
    "list_runs",
    "run_workflow",
    "save_run",
]

_register_extension_recipes()
