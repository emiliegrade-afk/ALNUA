"""Context building and learning hooks for fix_pipeline retries."""
from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from agents.fix_pipeline_constants import CONTEXT_LEVELS

logger = logging.getLogger(__name__)


def _build_context(error: dict, repo_path: str, attempt: int) -> dict[str, Any]:
    """
    Construit un contexte de plus en plus riche selon le numéro de tentative.
    Cœur du système d'apprentissage itératif.
    """
    level = CONTEXT_LEVELS[min(attempt, len(CONTEXT_LEVELS) - 1)]
    context: dict[str, Any] = {
        "error": error,
        "attempt": attempt + 1,
        "level": level["depth"],
    }

    try:
        from skills.skill_error_journal import get_error_history

        context["history"] = get_error_history(
            agent_name=error.get("agent_name", ""),
            error_type=error.get("error_type", ""),
            limit=level["history"],
        )
    except Exception:
        context["history"] = []

    try:
        from skills.skill_agent_learning import get_learning_context, memory_agent_id

        agent_name = error.get("agent_name", "dev_app")
        query = f"fix {error.get('error_type', '')} {error.get('error_message', '')[:100]}"
        context["memory"] = get_learning_context(memory_agent_id(agent_name), query)
    except Exception:
        context["memory"] = ""

    if attempt >= 1 and repo_path:
        root = Path(repo_path)
        extra_files = {}
        py_files = sorted(root.rglob("*.py"), key=lambda p: p.stat().st_mtime, reverse=True)
        for pf in py_files[: level["files"]]:
            if ".git" not in str(pf) and "__pycache__" not in str(pf):
                try:
                    rel = str(pf.relative_to(root))
                    extra_files[rel] = pf.read_text(encoding="utf-8", errors="ignore")[:2000]
                except Exception:
                    pass
        context["extra_files"] = extra_files

    return context


def _record_attempt(error_id: str, attempt: int, result: str, learned: str) -> None:
    """Enregistre ce qu'on a appris de cette tentative."""
    try:
        from skills.skill_error_journal import add_attempt_note

        add_attempt_note(error_id, attempt=attempt, note=f"Tentative {attempt+1}: {result} | Appris: {learned}")
    except Exception:
        pass


def _record_failure_learning(error: dict, attempt: int, reason: str, learned: str) -> None:
    """Distille et enregistre chaque échec intermédiaire dans Mem0."""
    try:
        from skills.skill_agent_learning import learn_from_failure, memory_agent_id

        agent_name = memory_agent_id(error.get("agent_name", "dev_app"))
        err_type = error.get("error_type", "unknown")
        learn_from_failure(
            agent_id=agent_name,
            task=(
                f"fix {err_type} (tentative {attempt + 1}): "
                f"{error.get('error_message', '')[:200]}"
            ),
            error=f"{reason}: {learned[:400]}",
        )
    except Exception as exc:
        logger.warning("fix_pipeline: failure learning failed: %s", exc)


def _record_resolution(error: dict, fix_summary: str, diff: str) -> None:
    """
    Enregistre le fix réussi dans Mem0 — apprentissage ciblé par domaine.
    """
    try:
        from skills.skill_agent_learning import learn_from_outcome, memory_agent_id
        from skills.skill_mem0 import remember

        agent_name = memory_agent_id(error.get("agent_name", ""))
        err_type = error.get("error_type", "erreur")

        if agent_name:
            remember(
                f"[Apprentissage propre] Bug '{err_type}' résolu : {fix_summary[:400]}. "
                f"Ne plus répéter cette erreur — contexte : {error.get('error_message', '')[:200]}",
                agent_id=agent_name,
            )
            learn_from_outcome(
                agent_id=agent_name,
                task=f"fix {err_type}",
                outcome=fix_summary,
                success=True,
            )

        remember(
            f"[Pattern QA] Fix type '{err_type}' validé : {fix_summary[:200]}. "
            f"Critères qui ont permis l'approbation — fix minimal, ciblé, tests verts.",
            agent_id="qa",
        )

        remember(
            f"[Pattern Spec] Correction architecturale approuvée pour '{err_type}' "
            f"(agent {agent_name}) : {fix_summary[:200]}.",
            agent_id="spec",
        )

        remember(
            f"[Supervision] Bug '{err_type}' de {agent_name} auto-résolu. "
            f"Résumé : {fix_summary[:150]}. Système autonome opérationnel.",
            agent_id="coo",
        )

        logger.info(
            "fix_pipeline: apprentissage ciblé — %s + qa + spec + coo",
            agent_name,
        )
    except Exception as exc:
        logger.warning("fix_pipeline: record_resolution failed: %s", exc)
