"""Main fix_pipeline orchestration loop."""
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
    """
    Pipeline de fix autonome complet. Appelé par bug_watchdog.

    Max WATCHDOG_MAX_ATTEMPTS tentatives — contexte croissant à chaque retry.
    Chaque tentative ratée enrichit le journal et Mem0.
    Merge automatique uniquement si QA + Spec + tests sont verts.

    Returns:
        {"resolved": bool, "attempts": int, "pr_url": str|None, "summary": str}
    """
    from skills.skill_agent_learning import memory_agent_id
    from skills.skill_code_agent import fix_bug
    from skills.skill_error_journal import increment_attempts, mark_escalated, mark_resolved

    error_id = error["id"]
    error_message = error.get("error_message", "")
    agent_name = error.get("agent_name", "unknown")
    fix_agent_id = memory_agent_id(agent_name if agent_name != "unknown" else "dev_app")
    err_type = error.get("error_type", "unknown")

    deploy_info = _detect_deploy_method(repo_path)
    logger.info("fix_pipeline: déploiement détecté → %s (%s)", deploy_info["method"], deploy_info["name"])

    try:
        readme = (Path(repo_path) / "README.md").read_text(encoding="utf-8", errors="ignore")[:800]
    except Exception:
        readme = f"Repo ALNUA Hub — agent {agent_name}"

    attempt = 0
    last_branch = None

    while attempt < MAX_PIPELINE_ATTEMPTS:
        logger.info(
            "fix_pipeline: tentative %d/%d pour erreur %s",
            attempt + 1,
            MAX_PIPELINE_ATTEMPTS,
            error_id[:8],
        )
        increment_attempts(error_id)

        context = _build_context(error, repo_path, attempt)
        error_context = (
            f"Tentative {attempt+1} | Niveau contexte: {context['level']}\n"
            f"Historique similaire: {len(context.get('history', []))} erreurs\n"
            f"Mémoire agents: {context.get('memory', '')[:300]}"
        )

        if last_branch:
            _rollback(repo_path, last_branch)

        loop = asyncio.get_event_loop()
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

        if not result.get("success"):
            learned = f"CodeAgent n'a pas pu générer un fix: {result.get('summary', '')[:200]}"
            _record_attempt(error_id, attempt, "échec generation", learned)
            _record_failure_learning(error, attempt, "échec generation", learned)
            logger.warning("fix_pipeline: génération fix échouée — retry avec plus de contexte")
            attempt += 1
            await asyncio.sleep(5)
            continue

        fix_summary = result.get("summary", "Fix appliqué")
        last_branch = result.get("branch")

        test_result = await loop.run_in_executor(None, lambda: _run_tests(repo_path))

        if not test_result["passed"]:
            learned = (
                f"Fix '{fix_summary[:100]}' a cassé les tests. "
                f"Output: {test_result['output'][:300]}"
            )
            _record_attempt(error_id, attempt, "tests échoués", learned)
            _record_failure_learning(error, attempt, "tests échoués", learned)
            error["error_message"] = (
                f"{error_message}\n\n[TENTATIVE {attempt+1} ÉCHOUÉE — Tests output:]\n{test_result['output'][:500]}"
            )
            logger.warning("fix_pipeline: tests ratés — retry avec output tests dans contexte")
            attempt += 1
            await asyncio.sleep(5)
            continue

        diff = _get_diff(repo_path, last_branch) if last_branch else ""
        qa = await loop.run_in_executor(
            None, lambda: _qa_review(diff, error_message, fix_summary)
        )

        if not qa.get("approved"):
            learned = f"QA rejeté: {qa.get('feedback', '')}"
            _record_attempt(error_id, attempt, "QA rejeté", learned)
            _record_failure_learning(error, attempt, "QA rejeté", learned)
            error["error_message"] = (
                f"{error_message}\n\n[QA FEEDBACK tentative {attempt+1}:]\n{qa.get('feedback', '')}"
            )
            logger.warning("fix_pipeline: QA a rejeté le fix — retry")
            attempt += 1
            await asyncio.sleep(5)
            continue

        spec = await loop.run_in_executor(
            None, lambda: _spec_review(diff, fix_summary, readme)
        )

        if not spec.get("approved"):
            learned = f"Spec rejeté: {spec.get('feedback', '')}"
            _record_attempt(error_id, attempt, "Spec rejeté", learned)
            _record_failure_learning(error, attempt, "Spec rejeté", learned)
            error["error_message"] = (
                f"{error_message}\n\n[SPEC FEEDBACK tentative {attempt+1}:]\n{spec.get('feedback', '')}"
            )
            logger.warning("fix_pipeline: Spec a rejeté le fix — retry")
            attempt += 1
            await asyncio.sleep(5)
            continue

        logger.info("fix_pipeline: ✅ fix validé (tentative %d) — merge + deploy", attempt + 1)

        merged = False
        if last_branch:
            merged = await loop.run_in_executor(None, lambda: _auto_merge(repo_path, last_branch))

        deployed = False
        if merged:
            deployed = await loop.run_in_executor(None, lambda: _restart_app(repo_path, deploy_info))

        _record_resolution(error, fix_summary, diff)
        mark_resolved(error_id, solution=fix_summary)

        status_line = "✅ déployé automatiquement" if deployed else "✅ mergé (redémarrage manuel requis)"
        pr_url = result.get("pr_url", "")
        await _notify(
            f"🤖 Bug auto-résolu — {agent_name}\n"
            f"Type: {err_type}\n"
            f"Fix ({attempt+1} tentative{'s' if attempt > 0 else ''}) : {fix_summary[:200]}\n"
            f"{status_line}"
            + (f"\nPR: {pr_url}" if pr_url else "")
        )

        return {
            "resolved": True,
            "attempts": attempt + 1,
            "pr_url": pr_url,
            "summary": fix_summary,
            "deployed": deployed,
        }

    mark_escalated(error_id)
    await _notify(
        f"⚠️ Bug non résolu — {agent_name}\n"
        f"Type: {err_type}\n"
        f"{MAX_PIPELINE_ATTEMPTS} tentatives épuisées — escalade COO requise."
    )
    logger.warning(
        "fix_pipeline: escalade après %d tentatives pour %s",
        MAX_PIPELINE_ATTEMPTS,
        error_id[:8],
    )
    return {
        "resolved": False,
        "attempts": attempt,
        "pr_url": None,
        "summary": f"Escaladé après {MAX_PIPELINE_ATTEMPTS} tentatives",
    }
