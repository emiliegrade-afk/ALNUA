"""Main fix_pipeline orchestration — Loop Engine (DEC-024)."""

from __future__ import annotations

import asyncio
import logging
from pathlib import Path
from typing import Any

from agents.fix_pipeline_constants import FIX_MODEL, MAX_PIPELINE_ATTEMPTS
from agents.fix_pipeline_context import (
    _build_context,
    _record_attempt,
    _record_failure_learning,
    _record_resolution,
)
from agents.fix_pipeline_deploy import _detect_deploy_method, _restart_app, _run_tests
from agents.fix_pipeline_git import _auto_merge, _get_diff, _rollback
from agents.fix_pipeline_notify import _notify
from agents.fix_pipeline_reviews import _qa_review, _spec_review

logger = logging.getLogger(__name__)


async def run(error: dict[str, Any], repo_path: str, github_repo: str | None = None) -> dict[str, Any]:
    """Pipeline de fix autonome — Loop Engine + isolation Phase A."""
    from services.agent_isolation import LockBusyError, SlotBusyError, task_isolation
    from skills.skill_agent_learning import memory_agent_id

    error_id = error["id"]
    agent_name = error.get("agent_name", "unknown")
    fix_agent_id = memory_agent_id(agent_name if agent_name != "unknown" else "dev_app")

    try:
        with task_isolation(
            agent_id=fix_agent_id,
            holder_id=f"fix:{error_id}",
            lock_keys=[f"task:{error_id}"],
            kwargs={"error_id": error_id, "task_id": error_id},
            repo_path=repo_path,
            meta={"kind": "fix_pipeline"},
        ):
            return await _run_isolated(error, repo_path, github_repo, fix_agent_id)
    except (LockBusyError, SlotBusyError) as exc:
        logger.warning("fix_pipeline: isolation busy for %s — %s", error_id[:8], exc)
        return {
            "resolved": False,
            "attempts": 0,
            "pr_url": None,
            "summary": f"Isolation busy: {exc}",
        }


async def _run_isolated(
    error: dict[str, Any],
    repo_path: str,
    github_repo: str | None,
    fix_agent_id: str,
) -> dict[str, Any]:
    from services.loop_engine import EvalVerdict, LoopContext, resolve_max_iterations, run_loop_async
    from skills.skill_code_agent import fix_bug
    from skills.skill_error_journal import increment_attempts, mark_escalated, mark_resolved

    error_id = error["id"]
    base_error_message = error.get("error_message", "")
    agent_name = error.get("agent_name", "unknown")
    err_type = error.get("error_type", "unknown")
    # Destructive path ends in merge/deploy → strict ceiling (DEC-024)
    loop_cap = resolve_max_iterations(strict=True, override=MAX_PIPELINE_ATTEMPTS)
    deploy_info = _detect_deploy_method(repo_path)
    logger.info("fix_pipeline: déploiement détecté → %s (%s)", deploy_info["method"], deploy_info["name"])

    try:
        readme = (Path(repo_path) / "README.md").read_text(encoding="utf-8", errors="ignore")[:800]
    except Exception:
        readme = f"Repo ALNUA Hub — agent {agent_name}"

    last_branch: str | None = None
    loop = asyncio.get_event_loop()

    async def execute(ctx: LoopContext) -> dict[str, Any]:
        nonlocal last_branch
        attempt_idx = ctx.iteration - 1
        increment_attempts(error_id)
        context = _build_context(error, repo_path, attempt_idx)
        feedback_extra = ctx.feedback_block(max_chars=1500)
        error_context = (
            f"Tentative {ctx.iteration} | Niveau contexte: {context['level']}\n"
            f"Historique similaire: {len(context.get('history', []))} erreurs\n"
            f"Mémoire agents: {context.get('memory', '')[:300]}\n"
            f"{feedback_extra}"
        )
        error_message = base_error_message
        if feedback_extra:
            error_message = f"{base_error_message}\n\n{feedback_extra}"

        if last_branch:
            _rollback(repo_path, last_branch)
            last_branch = None

        result = await loop.run_in_executor(
            None,
            lambda: fix_bug(
                error_message=error_message,
                error_context=error_context,
                repo_path=repo_path,
                github_repo=github_repo,
                model=FIX_MODEL,
                agent_id=fix_agent_id,
                dry_run=False,
            ),
        )
        return {
            "gen": result,
            "attempt_idx": attempt_idx,
            "error_message": error_message,
        }

    async def evaluate(payload: dict[str, Any], ctx: LoopContext) -> EvalVerdict:
        nonlocal last_branch
        result = payload["gen"]
        attempt_idx = int(payload["attempt_idx"])
        error_message = str(payload["error_message"])

        if not result.get("success"):
            learned = f"CodeAgent n'a pas pu générer un fix: {result.get('summary', '')[:200]}"
            _record_attempt(error_id, attempt_idx, "échec generation", learned)
            _record_failure_learning(error, attempt_idx, "échec generation", learned)
            return EvalVerdict(approved=False, feedback=learned)

        fix_summary = result.get("summary", "Fix appliqué")
        last_branch = result.get("branch")
        test_result = await loop.run_in_executor(None, lambda: _run_tests(repo_path))
        if not test_result["passed"]:
            learned = (
                f"Fix '{fix_summary[:100]}' a cassé les tests. "
                f"Output: {test_result['output'][:300]}"
            )
            _record_attempt(error_id, attempt_idx, "tests échoués", learned)
            _record_failure_learning(error, attempt_idx, "tests échoués", learned)
            return EvalVerdict(
                approved=False,
                feedback=f"Tests failed:\n{test_result['output'][:500]}",
            )

        diff = _get_diff(repo_path, last_branch) if last_branch else ""
        qa = await loop.run_in_executor(
            None, lambda: _qa_review(diff, error_message, fix_summary)
        )
        if not qa.get("approved"):
            learned = f"QA rejeté: {qa.get('feedback', '')}"
            _record_attempt(error_id, attempt_idx, "QA rejeté", learned)
            _record_failure_learning(error, attempt_idx, "QA rejeté", learned)
            return EvalVerdict(approved=False, feedback=learned)

        spec = await loop.run_in_executor(
            None, lambda: _spec_review(diff, fix_summary, readme)
        )
        if not spec.get("approved"):
            learned = f"Spec rejeté: {spec.get('feedback', '')}"
            _record_attempt(error_id, attempt_idx, "Spec rejeté", learned)
            _record_failure_learning(error, attempt_idx, "Spec rejeté", learned)
            return EvalVerdict(approved=False, feedback=learned)

        payload["fix_summary"] = fix_summary
        payload["diff"] = diff
        payload["pr_url"] = result.get("pr_url", "")
        return EvalVerdict(approved=True, meta={"detail": "tests+qa+spec"})

    loop_result = await run_loop_async(
        execute=execute,
        evaluate=evaluate,
        max_iterations=loop_cap,
        loop_id=f"fix:{error_id[:12]}",
        sleep_s=5.0,
        meta={"error_id": error_id, "agent": agent_name},
    )

    if loop_result.success and loop_result.value:
        payload = loop_result.value
        gen = payload.get("gen") or {}
        fix_summary = str(
            payload.get("fix_summary") or gen.get("summary") or "Fix appliqué"
        )
        diff = str(payload.get("diff") or "")
        pr_url = str(payload.get("pr_url") or gen.get("pr_url") or "")
        logger.info(
            "fix_pipeline: ✅ fix validé (tentative %d) — merge + deploy",
            loop_result.iterations,
        )
        merged = False
        if last_branch:
            merged = await loop.run_in_executor(
                None, lambda: _auto_merge(repo_path, last_branch)
            )
        deployed = False
        if merged:
            deployed = await loop.run_in_executor(
                None, lambda: _restart_app(repo_path, deploy_info)
            )
        _record_resolution(error, fix_summary, diff)
        mark_resolved(error_id, solution=fix_summary)
        status_line = (
            "✅ déployé automatiquement"
            if deployed
            else "✅ mergé (redémarrage manuel requis)"
        )
        await _notify(
            f"🤖 Bug auto-résolu — {agent_name}\n"
            f"Type: {err_type}\n"
            f"Fix ({loop_result.iterations} tentative"
            f"{'s' if loop_result.iterations > 1 else ''}) : {fix_summary[:200]}\n"
            f"{status_line}"
            + (f"\nPR: {pr_url}" if pr_url else "")
        )
        return {
            "resolved": True,
            "attempts": loop_result.iterations,
            "pr_url": pr_url,
            "summary": fix_summary,
            "deployed": deployed,
            "loop": loop_result.to_dict(),
        }

    mark_escalated(error_id)
    await _notify(
        f"⚠️ Bug non résolu — {agent_name}\n"
        f"Type: {err_type}\n"
        f"{loop_cap} tentatives épuisées — escalade COO requise."
    )
    logger.warning(
        "fix_pipeline: escalade après %d tentatives pour %s (%s)",
        loop_result.iterations,
        error_id[:8],
        loop_result.status,
    )
    return {
        "resolved": False,
        "attempts": loop_result.iterations,
        "pr_url": None,
        "summary": loop_result.escalate_reason
        or f"Escaladé après {loop_cap} tentatives",
        "loop": loop_result.to_dict(),
    }
