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


def _run_has_a_verifier(run: WorkflowRun) -> bool:
    return any(s.status == "A_VERIFIER" for s in run.steps)


def list_runs(
    *,
    limit: int = 30,
    recipe_id: str | None = None,
    waiting_a_verifier: bool = False,
) -> list[dict[str, Any]]:
    items: list[tuple[str, WorkflowRun]] = []
    for path in sorted(_runs_dir().glob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True):
        try:
            run = WorkflowRun.model_validate(json.loads(path.read_text(encoding="utf-8")))
            if recipe_id and run.recipe_id != recipe_id:
                continue
            if waiting_a_verifier and not _run_has_a_verifier(run):
                continue
            items.append((path.name, run))
        except Exception:
            continue
        if len(items) >= limit:
            break
    out: list[dict[str, Any]] = []
    for _, run in items:
        row: dict[str, Any] = {
            "run_id": run.run_id,
            "recipe_id": run.recipe_id,
            "status": run.status,
            "blocked_at_step": run.blocked_at_step,
            "created_at": run.created_at,
            "finished_at": run.finished_at,
            "summary": run.summary[:200],
        }
        if waiting_a_verifier:
            row["steps_a_verifier"] = [
                {
                    "step_id": s.step_id,
                    "label": s.label,
                    "detail": (s.detail or "")[:200],
                }
                for s in run.steps
                if s.status == "A_VERIFIER"
            ]
        out.append(row)
    return out
