"""Workflow engine — run persistence."""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

from services.workflow_engine_models import WorkflowRun

logger = logging.getLogger(__name__)


def _runs_dir() -> Path:
    from services import workflow_engine as we

    base: Path = we._RUNS_DIR
    base.mkdir(parents=True, exist_ok=True)
    return base


def save_run(run: WorkflowRun) -> Path:
    path = _runs_dir() / f"{run.run_id}.json"
    path.write_text(json.dumps(run.model_dump(), indent=2, ensure_ascii=False), encoding="utf-8")
    return path


def get_run(run_id: str) -> WorkflowRun | None:
    path = _runs_dir() / f"{run_id}.json"
    if not path.exists():
        return None
    try:
        return WorkflowRun.model_validate(json.loads(path.read_text(encoding="utf-8")))
    except Exception as exc:
        logger.warning("workflow get_run failed: %s", exc)
        return None


def list_runs(*, limit: int = 30, recipe_id: str | None = None) -> list[dict[str, Any]]:
    items: list[tuple[str, WorkflowRun]] = []
    for path in sorted(_runs_dir().glob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True):
        try:
            run = WorkflowRun.model_validate(json.loads(path.read_text(encoding="utf-8")))
            if recipe_id and run.recipe_id != recipe_id:
                continue
            items.append((path.name, run))
        except Exception:
            continue
        if len(items) >= limit:
            break
    return [
        {
            "run_id": run.run_id,
            "recipe_id": run.recipe_id,
            "status": run.status,
            "blocked_at_step": run.blocked_at_step,
            "created_at": run.created_at,
            "finished_at": run.finished_at,
            "summary": run.summary[:200],
        }
        for _, run in items
    ]
