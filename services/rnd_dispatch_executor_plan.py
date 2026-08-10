"""Build execution plans from CEO dispatch matrix."""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any

from services.agent_pipeline_registry import PIPELINE_METHODS
from services.plan_executor import ExecutionPlan, ExecutionStep
from services.rnd_schemas import RndDossierOut

from services.rnd_dispatch_executor_helpers import (
    normalize_dispatch_agent_id,
    task_instruction,
    workspace_root_str,
)

logger = logging.getLogger(__name__)


def create_spec_ticket(
    db: Any,
    dossier: RndDossierOut,
    project_id: str | None,
) -> dict[str, Any]:
    """Cree (ou retrouve) un ticket Supabase pour le dispatch spec."""
    slug = dossier.slug or dossier.id
    ticket: dict[str, Any] = {
        "title": f"[Dispatch Spec] {dossier.title}"[:200],
        "description": (
            f"Spec dispatch automatique pour le projet CEO : {dossier.title}.\n"
            f"Slug workspace : {slug}\n"
            f"Brief : {(dossier.one_pager_md or '')[:500]}"
        ),
        "project_id": project_id,
        "priority": "high",
        "type": "spec",
        "source": "rnd_dispatch",
        "status": "open",
        "workspace_slug": slug,
    }
    try:
        created = db.insert("tickets", ticket)
        if created and isinstance(created, (list, dict)):
            row = created[0] if isinstance(created, list) else created
            ticket["id"] = row.get("id")
            logger.info("Ticket spec cree : %s", ticket["id"])
    except Exception as exc:
        logger.warning("create_spec_ticket failed (fallback sans id): %s", exc)
    return ticket


def step_for_row(
    dossier: RndDossierOut,
    row: dict[str, Any],
    package: dict[str, Any],
    project_id: str | None,
    step_index: int,
    workspace_path: str,
    db: Any,
) -> ExecutionStep | None:
    agent_id = normalize_dispatch_agent_id(str(row.get("agent_id") or ""))
    if not agent_id or agent_id == "coo":
        return None

    instruction = task_instruction(dossier, row, package, agent_id, workspace_path)
    pole = row.get("pole", agent_id)
    slug = dossier.slug or dossier.id

    if agent_id == "spec":
        ticket = create_spec_ticket(db, dossier, project_id)
        ticket["description"] = instruction
        return ExecutionStep(
            step_id=str(step_index),
            description=f"Spec — {pole}",
            agent_id="spec",
            method="generate_and_write_dispatch",
            kwargs={
                "ticket": ticket,
                "project_info": {
                    "name": dossier.title,
                    "slug": slug,
                    "description": dossier.one_pager_md or "",
                },
            },
            depends_on=["1"],
        )

    if agent_id == "accounting":
        fj = dossier.finance_json or {}
        month = datetime.now(timezone.utc).strftime("%Y-%m")
        return ExecutionStep(
            step_id=str(step_index),
            description=f"Compta — {pole}",
            agent_id="accounting",
            method="financial_advice",
            kwargs={
                "month": month,
                "financial_summary": fj,
                "question": (
                    f"Projet {dossier.title} — valide le business case CEO et "
                    "recommande la prochaine etape finance.\n\n"
                    f"Instructions : {instruction}"
                ),
            },
            depends_on=["1"],
        )

    methods = PIPELINE_METHODS.get(agent_id, [])
    method = "handle_instruction" if "handle_instruction" in methods else (methods[0] if methods else None)
    if not method:
        logger.warning("No pipeline method for dispatch agent %s", agent_id)
        return None

    kwargs: dict[str, Any] = {"instruction": instruction}
    if agent_id == "pm" and project_id:
        kwargs["project_id"] = project_id

    return ExecutionStep(
        step_id=str(step_index),
        description=f"{pole}",
        agent_id=agent_id,
        method=method,
        kwargs=kwargs,
        depends_on=["1"],
    )


def build_dispatch_execution_plan(
    dossier: RndDossierOut,
    matrix: list[dict[str, Any]],
    package: dict[str, Any],
    project_id: str | None,
    workspace_path: str = "",
    db: Any = None,
) -> ExecutionPlan:
    """Deterministic plan from CEO dispatch matrix (no extra COO LLM parse)."""
    if not workspace_path:
        workspace_path = workspace_root_str()

    steps: list[ExecutionStep] = []
    idx = 1

    steps.append(
        ExecutionStep(
            step_id=str(idx),
            description=f"Orchestration COO — {dossier.title}",
            agent_id="coo",
            method="handle_instruction",
            kwargs={
                "instruction": (
                    f"Projet CEO valide : {dossier.title}. "
                    f"Lance la phase conception — coordonne PM, Spec, Dev, Marketing, Compta. "
                    f"{len(matrix)} poles dans la matrice dispatch. "
                    f"Workspace disque : {workspace_path}/"
                ),
                "project": dossier.title,
            },
            depends_on=[],
        )
    )
    idx += 1

    for row in matrix:
        if str(row.get("agent_id")) in ("coo_agent", "coo"):
            continue
        step = step_for_row(dossier, row, package, project_id, idx, workspace_path, db)
        if step:
            steps.append(step)
            idx += 1

    return ExecutionPlan(
        title=f"Conception — {dossier.title}",
        steps=steps,
        objective=f"Lancer conception post-validation CEO : {dossier.title}",
        context=dossier.slug or dossier.id,
    )
