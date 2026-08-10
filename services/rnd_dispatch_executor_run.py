"""Synchronous dispatch execution — plan run, deliverables, manifest, validation."""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from services.plan_executor import execute_plan
from services.rnd_ceo_package import resolve_branch
from services.rnd_dispatch_playbooks import all_required_files, get_playbook
from services.rnd_schemas import RndDossierOut
from services.rnd_workspace import (
    finalize_manifest,
    init_manifest,
    init_project_workspace,
    missing_deliverables,
    update_manifest_agent,
    validate_deliverables,
    write_deliverable,
)

from services.rnd_dispatch_executor_deliverables import (
    create_dev_app_scaffold,
    validate_pm_step,
    write_playbook_deliverables,
)
from services.rnd_dispatch_executor_helpers import extract_text_output, write_agent_log, workspace_root_str
from services.rnd_dispatch_executor_plan import build_dispatch_execution_plan

logger = logging.getLogger(__name__)


def run_dispatch_execution(
    dossier: RndDossierOut,
    matrix: list[dict[str, Any]],
    package: dict[str, Any],
    project_id: str | None,
    db: Any,
) -> dict[str, Any]:
    """Run dispatch plan synchronously — agents travaillent + fichiers ecrits sur disque."""
    slug = dossier.slug or dossier.id
    workspace_root = workspace_root_str()

    try:
        _workspace_paths = init_project_workspace(slug)
        logger.info("Workspace init OK : %s/{pole}/%s/", workspace_root, slug)
    except Exception as exc:
        logger.error("init_project_workspace failed: %s", exc)

    try:
        init_manifest(slug, dossier.title, Path(workspace_root), matrix)
    except Exception as exc:
        logger.warning("init_manifest failed: %s", exc)

    plan = build_dispatch_execution_plan(
        dossier, matrix, package, project_id, workspace_root, db
    )
    if len(plan.steps) <= 1:
        return {
            "error": "Plan vide",
            "plan": plan.to_dict(),
            "results": [],
            "workspace": workspace_root,
        }

    for step in plan.steps:
        write_agent_log(
            db,
            agent_id=step.agent_id,
            action="rnd_dispatch_execute",
            status="pending",
            summary=step.description,
            project_id=project_id,
        )

    result = execute_plan(plan, max_concurrent=4, stop_on_failure=False, max_retries=1)

    dispatched_agent_ids: list[str] = []

    for step_result in result.get("results") or []:
        if not isinstance(step_result, dict):
            continue
        aid = step_result.get("agent_id", "")
        ok = step_result.get("success", False)
        raw_output = step_result.get("result")
        err = step_result.get("error") or ""
        output_text = extract_text_output(raw_output)

        if not ok or not output_text.strip():
            write_agent_log(
                db,
                agent_id=aid,
                action="rnd_dispatch_execute",
                status="error",
                summary=err or "no output",
                project_id=project_id,
            )
            update_manifest_agent(slug, aid, status="error", error=err[:200] if err else "no output")
            continue

        if aid == "pm" and project_id:
            pm_valid = validate_pm_step(db, project_id, slug)
            if not pm_valid:
                logger.warning("PM dispatch: ticket ou roadmap absent en base pour %s", slug)
                update_manifest_agent(slug, aid, status="error", error="ticket ou roadmap absent en base")
                write_agent_log(
                    db,
                    agent_id=aid,
                    action="rnd_dispatch_execute",
                    status="error",
                    summary="ticket ou roadmap absent en base apres handle_instruction",
                    project_id=project_id,
                )
                continue

        dossier_branch = resolve_branch(dossier)
        playbook = get_playbook(aid, branch=dossier_branch)
        written_files: list[str] = []

        if (
            aid == "spec"
            and isinstance(raw_output, dict)
            and raw_output.get("file_path")
            and playbook
        ):
            written_files = list(playbook.files)
        elif playbook and aid != "coo":
            written_files = write_playbook_deliverables(slug, aid, output_text, playbook)
            if aid == "dev_app" and dossier_branch != "hub":
                create_dev_app_scaffold(slug, workspace_root)
        elif aid == "coo":
            coo_pb = get_playbook("coo", branch=dossier_branch)
            if coo_pb:
                written_files = write_playbook_deliverables(slug, "coo", output_text, coo_pb)
        else:
            try:
                write_deliverable("analytics", slug, f"{aid}-output.md", output_text)
                written_files = [f"analytics/{aid}-output.md"]
            except Exception as exc:
                logger.warning("Fallback write failed for %s: %s", aid, exc)

        if written_files and playbook:
            checks = validate_deliverables(slug, written_files)
            all_present = all(checks.values())
            missing_for_agent = [f for f, exists in checks.items() if not exists]

            log_status = "success" if all_present else "error"
            manifest_status = "success" if all_present else "partial"
            log_summary = (
                output_text
                if all_present
                else f"Fichiers manquants apres ecriture : {missing_for_agent}"
            )
        else:
            log_status = "success" if written_files else "error"
            manifest_status = "success" if written_files else "error"
            log_summary = output_text or err

        write_agent_log(
            db,
            agent_id=aid,
            action="rnd_dispatch_execute",
            status=log_status,
            summary=log_summary,
            project_id=project_id,
        )
        update_manifest_agent(slug, aid, status=manifest_status, files=written_files)
        if log_status == "success":
            dispatched_agent_ids.append(aid)

    required_files = all_required_files(dispatched_agent_ids, branch=resolve_branch(dossier))
    missing = missing_deliverables(slug, required_files) if required_files else []
    dispatch_success = len(missing) == 0

    finalize_manifest(slug, success=dispatch_success, missing=missing)

    if missing:
        logger.warning(
            "Dispatch %s partiel — fichiers manquants : %s",
            slug,
            ", ".join(missing),
        )
    else:
        logger.info("Dispatch %s complet — tous les livrables presents.", slug)

    workspace_validation: dict[str, Any] = {
        "success": dispatch_success,
        "missing_files": missing,
        "required_files": required_files,
        "completed_at": datetime.now(timezone.utc).isoformat(),
        "workspace_root": workspace_root,
        "convention": "ALNUA/{pole}/{slug}/{filename}",
    }
    try:
        db.update(
            "rnd_dossiers",
            dossier.id,
            {
                "workspace_path": f"{workspace_root}",
                "workspace_validation": workspace_validation,
            },
        )
    except Exception as exc:
        logger.warning("workspace_validation persist failed pour %s: %s", dossier.id, exc)

    result["workspace"] = workspace_root
    result["workspace_path"] = workspace_root
    result["validation"] = workspace_validation

    if resolve_branch(dossier) == "hub":
        try:
            from services.hub_dispatch_coding import create_hub_coding_issues

            coding = create_hub_coding_issues(
                dossier.title,
                slug,
                dossier_id=dossier.id,
            )
            result["hub_coding_issues"] = coding
            if coding.get("count"):
                logger.info(
                    "Hub dispatch: %s GitHub issue(s) created for %s",
                    coding["count"],
                    slug,
                )
        except Exception as exc:
            logger.warning("hub_dispatch_coding failed: %s", exc)
            result["hub_coding_issues"] = {"success": False, "error": str(exc)}

    return result
