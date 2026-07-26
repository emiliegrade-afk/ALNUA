"""Kick off real agent work after R&D CEO dispatch (plan_executor).

Phase 9 — Workspace dispatch :
- Chaque agent produit un livrable concret ecrit sur disque (ALNUA_WORKSPACE)
- Convention Option A : ALNUA/{pole}/{slug}/{filename}
- Playbooks definissent fichiers attendus + templates
- Manifest JSON trace les statuts par agent
- Validation finale : tous les fichiers requis doivent exister AVANT de marquer success
  dans agent_logs (item 5) et dans le manifest

Corrections Round 2 :
- Item 2 : spec utilise generate_and_write_dispatch + ticket Supabase cree avant
- Item 4 : PM — verifie ticket + roadmap en base apres handle_instruction
- Item 5 : agent_logs success SEULEMENT apres validate_deliverables() par agent
- Item 8 : persist workspace_validation sur rnd_dossier en fin d'execution
"""

from __future__ import annotations

import logging
import os
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from services.agent_pipeline_registry import LOG_NAME_TO_AGENT_ID, PIPELINE_METHODS
from services.plan_executor import ExecutionPlan, ExecutionStep, execute_plan
from services.rnd_ceo_package import resolve_branch
from services.rnd_dispatch_playbooks import (
    AgentPlaybook,
    all_required_files,
    build_instruction_with_paths,
    get_playbook,
)
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

logger = logging.getLogger(__name__)

# dispatch matrix agent_id -> pipeline agent_id
_DISPATCH_AGENT_ALIASES: dict[str, str] = {
    "pm_agent": "pm",
    "spec_agent": "spec",
    "qa_agent": "qa",
    "marketing_agent": "marketing",
    "accountant_agent": "accounting",
    "accounting": "accounting",
    "dev_app_agent": "dev_app",
    "dev_app": "dev_app",
    "dev_backend_agent": "dev_backend",
    "dev_gaming": "dev_gaming",
    "game_director": "game_director",
    "content_agent": "content",
    "content": "content",
    "hardware_agent": "hardware",
    "hardware": "hardware",
    "embedded_dev": "embedded_dev",
    "coo_agent": "coo",
    "coo": "coo",
}


def normalize_dispatch_agent_id(raw: str) -> str:
    key = (raw or "").strip()
    return _DISPATCH_AGENT_ALIASES.get(key, key.replace("_agent", ""))


def _workspace_root_str() -> str:
    """Retourne ALNUA_WORKSPACE root comme string (ne trigger pas config si env set)."""
    raw = os.environ.get("ALNUA_WORKSPACE", "").strip()
    if raw:
        return raw
    try:
        from config.paths import get_alnua_workspace
        return str(get_alnua_workspace())
    except Exception:
        import platform
        if platform.system() == "Windows":
            return "C:/Dev/ALNUA"
        from pathlib import Path as _P
        return str(_P.home() / "Dev" / "ALNUA")


def _task_instruction(
    dossier: RndDossierOut,
    row: dict[str, Any],
    package: dict[str, Any],
    agent_id: str,
    workspace_path: str,
) -> str:
    """Instruction enrichie avec paths workspace et template playbook."""
    excerpt = (package.get("markdown") or dossier.one_pager_md or "")[:3000]

    extra: dict[str, Any] = {}
    if agent_id == "accounting":
        extra["finance_json"] = dossier.finance_json or {}
    if agent_id in ("pm", "spec"):
        extra["pole"] = row.get("pole", "")
        extra["deliverables_attendus"] = ", ".join(row.get("deliverables") or [])

    return build_instruction_with_paths(
        agent_id=agent_id,
        dossier_title=dossier.title,
        slug=dossier.slug or dossier.id,
        workspace_path=workspace_path,
        context_excerpt=excerpt,
        extra=extra or None,
        branch=resolve_branch(dossier),
    )


# ---------------------------------------------------------------------------
# Item 2 — creation ticket Supabase pour spec
# ---------------------------------------------------------------------------

def _create_spec_ticket(
    db: Any,
    dossier: RndDossierOut,
    project_id: str | None,
) -> dict[str, Any]:
    """Cree (ou retrouve) un ticket Supabase pour le dispatch spec.

    Le ticket contient workspace_slug pour que spec_agent sache ou ecrire.
    Retourne le ticket dict (avec id si creation OK, sinon sans id pour fallback).
    """
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
        logger.warning("_create_spec_ticket failed (fallback sans id): %s", exc)
    return ticket


def _step_for_row(
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

    instruction = _task_instruction(dossier, row, package, agent_id, workspace_path)
    pole = row.get("pole", agent_id)
    slug = dossier.slug or dossier.id

    # Item 2 : spec utilise generate_and_write_dispatch + ticket Supabase
    if agent_id == "spec":
        ticket = _create_spec_ticket(db, dossier, project_id)
        ticket["description"] = instruction  # enrichit avec le template playbook
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
        workspace_path = _workspace_root_str()

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
        step = _step_for_row(dossier, row, package, project_id, idx, workspace_path, db)
        if step:
            steps.append(step)
            idx += 1

    return ExecutionPlan(
        title=f"Conception — {dossier.title}",
        steps=steps,
        objective=f"Lancer conception post-validation CEO : {dossier.title}",
        context=dossier.slug or dossier.id,
    )


def _agent_log_name(agent_id: str) -> str:
    for log_name, openroom_id in LOG_NAME_TO_AGENT_ID.items():
        if openroom_id == agent_id and log_name.endswith("_agent"):
            return log_name
    return f"{agent_id}_agent" if agent_id not in LOG_NAME_TO_AGENT_ID else agent_id


def _write_agent_log(
    db: Any,
    *,
    agent_id: str,
    action: str,
    status: str,
    summary: str,
    project_id: str | None,
) -> None:
    try:
        db.insert(
            "agent_logs",
            {
                "agent_name": _agent_log_name(agent_id),
                "action": action,
                "status": status,
                "project_id": project_id,
                "input_summary": summary[:4000],
                "output_summary": summary[:4000],
            },
        )
    except Exception as exc:
        logger.warning("agent log failed %s: %s", agent_id, exc)


def _extract_text_output(result: Any) -> str:
    """Extrait le contenu textuel d'un resultat agent (str, dict, CrewAI output)."""
    if isinstance(result, str):
        return result
    if hasattr(result, "raw"):
        return str(result.raw)
    if isinstance(result, dict):
        for key in ("content", "output", "result", "text", "markdown", "cursor_prompt",
                    "advice", "message", "summary", "report"):
            if isinstance(result.get(key), str) and result[key].strip():
                return result[key]
        return str(result)
    return str(result) if result is not None else ""


def _write_playbook_deliverables(
    slug: str,
    agent_id: str,
    output_text: str,
    playbook: AgentPlaybook,
) -> list[str]:
    """Ecrit les livrables sur disque selon le playbook (Option A : {pole}/{slug}/{filename}).

    Pour les agents avec 2 fichiers (pm, marketing), tente de splitter sur ---SPLIT---
    Sinon ecrit tout dans le fichier primaire.

    Returns: liste des chemins relatifs ecrits avec succes (format "pole/filename").
    """
    written: list[str] = []

    if len(playbook.files) == 1:
        try:
            filename = playbook.pole_relative_filename(0)
            # Option A : write_deliverable(pole, slug, filename, content)
            path = write_deliverable(playbook.pole, slug, filename, output_text)
            written.append(playbook.files[0])
            logger.info("Livrable %s ecrit : %s", agent_id, path)
        except Exception as exc:
            logger.error("Ecriture livrable %s echoue : %s", agent_id, exc)
        return written

    # Multi-fichiers : split sur ---SPLIT---
    parts = output_text.split("---SPLIT---")
    for i, filepath in enumerate(playbook.files):
        content = parts[i].strip() if i < len(parts) else output_text
        if not content:
            content = output_text
        filename = playbook.pole_relative_filename(i)
        try:
            # Option A : write_deliverable(pole, slug, filename, content)
            path = write_deliverable(playbook.pole, slug, filename, content)
            written.append(filepath)
            logger.info("Livrable %s[%d] ecrit : %s", agent_id, i, path)
        except Exception as exc:
            logger.error("Ecriture livrable %s[%d] echoue : %s", agent_id, i, exc)

    return written


def _create_dev_app_scaffold(slug: str, workspace_root: str) -> None:
    """Item 3 : cree un scaffold minimal pour dev_app dans app/{slug}/scaffold/."""
    import os as _os
    scaffold_dir = Path(workspace_root) / "app" / slug / "scaffold"
    try:
        scaffold_dir.mkdir(parents=True, exist_ok=True)

        readme = (
            f"# {slug} — Scaffold Next.js\n\n"
            "Structure generee automatiquement par ALNUA Hub (Phase 9).\n\n"
            "## Demarrage\n"
            "```bash\nnpm install\nnpm run dev\n```\n\n"
            "## Stack\n"
            "- Next.js 14 App Router\n"
            "- TypeScript\n"
            "- Tailwind CSS\n"
            "- shadcn/ui\n"
        )
        (scaffold_dir / "README.md").write_text(readme, encoding="utf-8")

        github_token = _os.environ.get("GITHUB_TOKEN", "").strip()
        coding_agent_note = (
            "true (GITHUB_TOKEN detecte — coding_agent peut initialiser le repo)"
            if github_token
            else "false (GITHUB_TOKEN absent — initialisation manuelle requise)"
        )

        pkg = (
            "{\n"
            f'  "name": "{slug}",\n'
            '  "version": "0.1.0",\n'
            '  "private": true,\n'
            f'  "description": "ALNUA project — coding_agent: {coding_agent_note}",\n'
            '  "scripts": {\n'
            '    "dev": "next dev",\n'
            '    "build": "next build",\n'
            '    "start": "next start",\n'
            '    "lint": "next lint"\n'
            '  },\n'
            '  "dependencies": {\n'
            '    "next": "14.x",\n'
            '    "react": "^18",\n'
            '    "react-dom": "^18"\n'
            '  },\n'
            '  "devDependencies": {\n'
            '    "typescript": "^5",\n'
            '    "@types/react": "^18",\n'
            '    "tailwindcss": "^3",\n'
            '    "autoprefixer": "^10",\n'
            '    "postcss": "^8"\n'
            '  }\n'
            "}\n"
        )
        (scaffold_dir / "package.json").write_text(pkg, encoding="utf-8")

        gitignore = (
            "node_modules/\n.next/\n.env\n.env.local\n.env*.local\n"
            "out/\nbuild/\ndist/\n*.log\n.DS_Store\n"
        )
        (scaffold_dir / ".gitignore").write_text(gitignore, encoding="utf-8")

        logger.info("dev_app scaffold cree : %s", scaffold_dir)
    except Exception as exc:
        logger.warning("_create_dev_app_scaffold failed: %s", exc)


def _validate_pm_step(db: Any, project_id: str | None, slug: str) -> bool:
    """Item 4 : apres handle_instruction PM, verifie le projet est cable en Hub.

    Roadmap obligatoire (creee au dispatch CEO). Ticket PM souhaite mais optionnel
    si la roadmap existe deja — le PM enrichit surtout les fichiers disque.
    """
    if not project_id or not db:
        return False
    try:
        roadmap_rows = db.select("roadmap", filters={"project_id": project_id}, limit=1)
        if not roadmap_rows:
            try:
                roadmap_rows = db.select("milestones", filters={"project_id": project_id}, limit=1)
            except Exception:
                roadmap_rows = []
        if not roadmap_rows:
            logger.warning(
                "PM validation: no roadmap/milestones for project_id=%s slug=%s",
                project_id,
                slug,
            )
            return False

        tickets = db.select("tickets", filters={"project_id": project_id}, limit=1)
        if not tickets:
            logger.info(
                "PM validation: roadmap OK, no ticket yet for project_id=%s slug=%s",
                project_id,
                slug,
            )
        return True
    except Exception as exc:
        logger.warning("PM validation query failed: %s", exc)
        return False


def run_dispatch_execution(
    dossier: RndDossierOut,
    matrix: list[dict[str, Any]],
    package: dict[str, Any],
    project_id: str | None,
    db: Any,
) -> dict[str, Any]:
    """Run dispatch plan synchronously — agents travaillent + fichiers ecrits sur disque.

    Item 5 : agent_logs success marque APRES validate_deliverables() par agent.
    Item 8 : workspace_validation persiste sur rnd_dossier en fin d'execution.
    """
    slug = dossier.slug or dossier.id
    workspace_root = _workspace_root_str()

    # --- Init workspace disque (Option A : retourne dict[pole, Path]) ---
    try:
        _workspace_paths = init_project_workspace(slug)
        logger.info("Workspace init OK : %s/{pole}/%s/", workspace_root, slug)
    except Exception as exc:
        logger.error("init_project_workspace failed: %s", exc)

    # --- Init manifest ---
    try:
        init_manifest(slug, dossier.title, Path(workspace_root), matrix)
    except Exception as exc:
        logger.warning("init_manifest failed: %s", exc)

    # --- Build execution plan (passe db pour creation ticket spec) ---
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

    # --- Log pending pour chaque agent ---
    for step in plan.steps:
        _write_agent_log(
            db,
            agent_id=step.agent_id,
            action="rnd_dispatch_execute",
            status="pending",
            summary=step.description,
            project_id=project_id,
        )

    # --- Execute ---
    result = execute_plan(plan, max_concurrent=4, stop_on_failure=False, max_retries=1)

    # --- Post-process : ecrire livrables + update manifest ---
    dispatched_agent_ids: list[str] = []

    for step_result in result.get("results") or []:
        if not isinstance(step_result, dict):
            continue
        aid = step_result.get("agent_id", "")
        ok = step_result.get("success", False)
        raw_output = step_result.get("result")
        err = step_result.get("error") or ""
        output_text = _extract_text_output(raw_output)

        if not ok or not output_text.strip():
            # Item 5 : log error immediatement (pas de fichiers a valider)
            _write_agent_log(
                db,
                agent_id=aid,
                action="rnd_dispatch_execute",
                status="error",
                summary=err or "no output",
                project_id=project_id,
            )
            update_manifest_agent(slug, aid, status="error", error=err[:200] if err else "no output")
            continue

        # Item 4 : validation PM apres handle_instruction
        if aid == "pm" and project_id:
            pm_valid = _validate_pm_step(db, project_id, slug)
            if not pm_valid:
                logger.warning("PM dispatch: ticket ou roadmap absent en base pour %s", slug)
                update_manifest_agent(slug, aid, status="error", error="ticket ou roadmap absent en base")
                _write_agent_log(
                    db,
                    agent_id=aid,
                    action="rnd_dispatch_execute",
                    status="error",
                    summary="ticket ou roadmap absent en base apres handle_instruction",
                    project_id=project_id,
                )
                continue

        # Ecriture disque via playbook
        dossier_branch = resolve_branch(dossier)
        playbook = get_playbook(aid, branch=dossier_branch)
        written_files: list[str] = []

        # Spec : generate_and_write_dispatch a deja ecrit le fichier
        if (
            aid == "spec"
            and isinstance(raw_output, dict)
            and raw_output.get("file_path")
            and playbook
        ):
            written_files = list(playbook.files)
        elif playbook and aid != "coo":
            written_files = _write_playbook_deliverables(slug, aid, output_text, playbook)
            # Item 3 : scaffold dev_app — external products only
            if aid == "dev_app" and dossier_branch != "hub":
                _create_dev_app_scaffold(slug, workspace_root)
        elif aid == "coo":
            coo_pb = get_playbook("coo", branch=dossier_branch)
            if coo_pb:
                written_files = _write_playbook_deliverables(slug, "coo", output_text, coo_pb)
        else:
            # Pas de playbook connu : dump brut dans analytics/
            try:
                # Option A : write_deliverable(pole, slug, filename, content)
                write_deliverable("analytics", slug, f"{aid}-output.md", output_text)
                written_files = [f"analytics/{aid}-output.md"]
            except Exception as exc:
                logger.warning("Fallback write failed for %s: %s", aid, exc)

        # Item 5 : valider les fichiers de CET agent avant de loger success
        if written_files and playbook:
            checks = validate_deliverables(slug, written_files)
            all_present = all(checks.values())
            missing_for_agent = [f for f, exists in checks.items() if not exists]

            log_status = "success" if all_present else "error"
            manifest_status = "success" if all_present else "partial"
            log_summary = (
                output_text if all_present
                else f"Fichiers manquants apres ecriture : {missing_for_agent}"
            )
        else:
            log_status = "success" if written_files else "error"
            manifest_status = "success" if written_files else "error"
            log_summary = output_text or err

        _write_agent_log(
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

    # --- Validation finale globale ---
    required_files = all_required_files(dispatched_agent_ids, branch=resolve_branch(dossier))
    missing = missing_deliverables(slug, required_files) if required_files else []
    dispatch_success = len(missing) == 0

    finalize_manifest(slug, success=dispatch_success, missing=missing)

    if missing:
        logger.warning(
            "Dispatch %s partiel — fichiers manquants : %s",
            slug, ", ".join(missing),
        )
    else:
        logger.info("Dispatch %s complet — tous les livrables presents.", slug)

    # Item 8 : persiste workspace_validation sur le dossier R&D en Supabase
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

    # Hub branch: CEO chose WHAT — auto-create coding issues (HOW)
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


def start_dispatch_execution_background(
    dossier: RndDossierOut,
    matrix: list[dict[str, Any]],
    package: dict[str, Any],
    project_id: str | None,
    db: Any,
    *,
    on_complete: Any | None = None,
) -> str:
    """Fire-and-forget thread — returns run label."""
    run_id = f"dispatch_{dossier.slug or dossier.id}_{int(datetime.now(timezone.utc).timestamp())}"

    def _worker() -> None:
        try:
            run_result = run_dispatch_execution(dossier, matrix, package, project_id, db)
            if on_complete:
                on_complete(run_result)
        except Exception as exc:
            logger.exception("dispatch execution failed for %s: %s", dossier.title, exc)
            _write_agent_log(
                db,
                agent_id="coo",
                action="rnd_dispatch_execute",
                status="error",
                summary=str(exc)[:4000],
                project_id=project_id,
            )

    threading.Thread(
        target=_worker,
        daemon=True,
        name=run_id,
    ).start()
    return run_id
