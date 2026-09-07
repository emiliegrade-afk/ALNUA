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


def _subject_from_context(ctx: dict[str, Any]) -> dict[str, Any]:
    """Human-readable linked object for CEO waiting queue (dossier, app, SAV…)."""
    dossier_id = str(ctx.get("dossier_id") or ctx.get("dossierId") or "").strip()
    slug = str(ctx.get("slug") or ctx.get("app_slug") or ctx.get("product_slug") or "").strip()
    title = str(
        ctx.get("title")
        or ctx.get("dossier_title")
        or ctx.get("name")
        or ctx.get("product_name")
        or ""
    ).strip()
    topic = str(ctx.get("topic") or "").strip()
    ticket_id = str(ctx.get("ticket_id") or ctx.get("sav_id") or "").strip()

    if dossier_id and not title:
        try:
            from services.rnd_repository import get_rnd_repository

            d = get_rnd_repository().get_dossier(dossier_id)
            if d is not None:
                title = getattr(d, "title", None) or ""
                if not slug:
                    slug = getattr(d, "slug", None) or ""
        except Exception:
            pass

    if dossier_id:
        label = title or slug or dossier_id[:12]
        return {
            "kind": "dossier",
            "label": label,
            "blurb": f"Idée / dossier R&D : {label}",
            "dossier_id": dossier_id,
            "slug": slug or None,
            "href": f"/rd?tab=dossiers&dossier={dossier_id}&view=ceo",
        }
    if slug:
        label = title or slug
        return {
            "kind": "app",
            "label": label,
            "blurb": f"Produit / projet : {label}",
            "slug": slug,
            "href": f"/apps?slug={slug}",
        }
    if ticket_id:
        return {
            "kind": "ticket",
            "label": title or ticket_id,
            "blurb": f"Ticket / SAV : {title or ticket_id}",
            "ticket_id": ticket_id,
            "href": f"/tickets?id={ticket_id}",
        }
    if topic:
        return {
            "kind": "topic",
            "label": topic,
            "blurb": f"Sujet : {topic}",
        }
    if title:
        return {"kind": "generic", "label": title, "blurb": title}
    return {
        "kind": "none",
        "label": "Sans objet lié",
        "blurb": "Cette procédure n’a pas de dossier / app attaché dans son contexte.",
    }


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
        subject = _subject_from_context(run.context if isinstance(run.context, dict) else {})
        row: dict[str, Any] = {
            "run_id": run.run_id,
            "recipe_id": run.recipe_id,
            "status": run.status,
            "blocked_at_step": run.blocked_at_step,
            "created_at": run.created_at,
            "finished_at": run.finished_at,
            "summary": run.summary[:280],
            "subject": subject,
            "context_keys": sorted(
                k for k in (run.context or {}) if not str(k).startswith("_")
            )[:20],
        }
        if waiting_a_verifier:
            row["steps_a_verifier"] = [
                {
                    "step_id": s.step_id,
                    "label": s.label,
                    "detail": (s.detail or "")[:500],
                    "gaps": list(s.gaps or [])[:8],
                }
                for s in run.steps
                if s.status == "A_VERIFIER"
            ]
        out.append(row)
    return out
