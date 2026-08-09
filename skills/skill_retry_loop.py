"""
skill_retry_loop.py

Intelligent retry loop for ALNUA agents.
Combines the error journal with exponential backoff retries.
"""

from __future__ import annotations

import logging
import time
import traceback
from collections.abc import Callable
from typing import Any

from skills.skill_error_journal import (
    build_retry_context,
    increment_attempts,
    log_error,
    mark_escalated,
    mark_resolved,
    search_similar_errors,
)
from config.llm_runtime import (
    RETRY_LOOP_DELAYS_S,
    RETRY_LOOP_MAX_ATTEMPTS,
    RETRY_LOOP_TOOL_MAX_ATTEMPTS,
)

logger = logging.getLogger(__name__)

MAX_ATTEMPTS_DEFAULT = RETRY_LOOP_MAX_ATTEMPTS
RETRY_DELAY_SECONDS = list(RETRY_LOOP_DELAYS_S)

# Errors where retrying the same LLM+tool path just burns tokens (auth / bad schema)
_NON_RETRYABLE_TYPES = frozenset({
    "PermissionError",
    "AuthError",
    "ToolSchemaError",
    "MCPError",
    "ComposioAuthError",
})


def classify_error(exception: Exception) -> str:
    """Classify an exception into a stable error type label."""
    name = type(exception).__name__
    msg = str(exception).lower()

    if "timeout" in msg or "TimeoutExpired" in name:
        return "TimeoutError"
    if "import" in msg or "ModuleNotFoundError" in name or "ImportError" in name:
        return "ImportError"
    if "permission" in msg or "PermissionError" in name or "403" in msg or "401" in msg:
        return "PermissionError"
    if "composio" in msg and ("auth" in msg or "oauth" in msg or "401" in msg):
        return "ComposioAuthError"
    if "mcp" in msg and ("tool" in msg or "schema" in msg or "unavailable" in msg):
        return "MCPError"
    if "tool" in msg and ("schema" in msg or "not found" in msg or "unknown tool" in msg):
        return "ToolSchemaError"
    if "connection" in msg or "ConnectionError" in name:
        return "ConnectionError"
    if "git" in msg or "worktree" in msg:
        return "GitError"
    if "syntax" in msg or "SyntaxError" in name:
        return "SyntaxError"
    if "api" in msg or "http" in msg:
        return "APIError"
    if "supabase" in msg or "database" in msg or "postgresql" in msg:
        return "DatabaseError"
    if "playwright" in msg or "browser" in msg:
        return "PlaywrightError"
    return name or "UnknownError"


def _effective_max_attempts(error_type: str | None, max_attempts: int) -> int:
    """Cap retries for tool/MCP auth failures — one shot, then escalate."""
    if error_type and error_type in _NON_RETRYABLE_TYPES:
        return min(max_attempts, RETRY_LOOP_TOOL_MAX_ATTEMPTS)
    return max_attempts


def retry_with_learning(
    agent_name: str,
    task_fn: Callable[[str], Any],
    task_id: str | None = None,
    task_context: str = "",
    max_attempts: int = MAX_ATTEMPTS_DEFAULT,
    telegram_notify_fn: Callable[[str], None] | None = None,
) -> dict[str, Any]:
    """
    Run task_fn with intelligent retries.

    task_fn receives a learning_context string to inject into the next prompt.
    """
    from skills.skill_agent_learning import (
        get_learning_context,
        learn_from_failure,
        learn_from_outcome,
        memory_agent_id,
    )

    canonical_agent = memory_agent_id(agent_name)
    last_error_id: str | None = None
    last_exception: Exception | None = None
    learning_context = get_learning_context(
        canonical_agent, task_context or task_id or agent_name
    )

    effective_max = max_attempts
    for attempt in range(1, max_attempts + 1):
        if attempt > effective_max:
            break
        logger.info(
            "[RetryLoop] %s — attempt %s/%s (task: %s)",
            agent_name,
            attempt,
            effective_max,
            task_id,
        )

        if attempt > 1 and attempt - 1 < len(RETRY_DELAY_SECONDS):
            delay = RETRY_DELAY_SECONDS[attempt - 1]
            if delay > 0:
                logger.info("[RetryLoop] Waiting %ss before retry...", delay)
                time.sleep(delay)

        try:
            result = task_fn(learning_context)

            if last_error_id:
                solution = (
                    f"Résolu à la tentative {attempt}. Contexte d'apprentissage utilisé : "
                    f"{learning_context[:300] if learning_context else 'Aucun'}"
                )
                mark_resolved(last_error_id, solution)
                logger.info(
                    "[RetryLoop] Success after %s attempt(s) — entry %s resolved",
                    attempt,
                    last_error_id,
                )

            if telegram_notify_fn and attempt > 1:
                telegram_notify_fn(
                    f"[OK] **{agent_name}** — Tâche `{task_id}` réussie après {attempt} tentative(s)"
                )

            learn_from_outcome(
                agent_id=canonical_agent,
                task=task_context or str(task_id or agent_name),
                outcome=str(result)[:600],
                success=True,
            )

            return {
                "success": True,
                "result": result,
                "attempts": attempt,
                "error": None,
                "escalated": False,
            }

        except Exception as exc:
            last_exception = exc
            error_type = classify_error(exc)
            effective_max = _effective_max_attempts(error_type, max_attempts)
            error_message = str(exc)
            full_traceback = traceback.format_exc()

            logger.warning(
                "[RetryLoop] %s — attempt %s failed: %s: %s",
                agent_name,
                attempt,
                error_type,
                error_message[:200],
            )
            if error_type in _NON_RETRYABLE_TYPES:
                logger.warning(
                    "[RetryLoop] %s — non-retryable %s — skip further LLM burns",
                    agent_name,
                    error_type,
                )

            similar = search_similar_errors(agent_name, error_message, error_type)

            if attempt == 1:
                last_error_id = log_error(
                    agent_name=agent_name,
                    error_type=error_type,
                    error_message=error_message,
                    context=f"{task_context}\n\nTraceback:\n{full_traceback[:500]}",
                    task_id=task_id,
                )
            elif last_error_id:
                increment_attempts(last_error_id)

            if similar:
                learning_context = build_retry_context(similar)
                logger.info(
                    "[RetryLoop] %s similar error(s) found — context injected for attempt %s",
                    len(similar),
                    attempt + 1,
                )
            else:
                learning_context = (
                    f"\n⚠️ Tentative {attempt} a échoué avec : "
                    f"{error_type}: {error_message[:300]}\n"
                    f"→ Essaie une approche différente pour éviter cette erreur.\n"
                )

            mem0_block = get_learning_context(
                canonical_agent,
                f"{error_type} {error_message[:200]}",
            )
            if mem0_block:
                learning_context = mem0_block + learning_context

            learn_from_failure(
                agent_id=canonical_agent,
                task=task_context or str(task_id or agent_name),
                error=f"{error_type}: {error_message[:400]}",
            )

            if telegram_notify_fn and attempt < effective_max:
                next_delay = (
                    RETRY_DELAY_SECONDS[attempt]
                    if attempt < len(RETRY_DELAY_SECONDS)
                    else 40
                )
                telegram_notify_fn(
                    f"⚠️ **{agent_name}** — Tentative {attempt}/{effective_max} échouée\n"
                    f"`{error_type}` : {error_message[:150]}\n"
                    f"🔄 Retry dans {next_delay}s..."
                )

    logger.error(
        "[RetryLoop] %s — task %s abandoned after %s attempts",
        agent_name,
        task_id,
        effective_max,
    )

    if last_error_id:
        mark_escalated(last_error_id)

    escalation_msg = (
        f"🚨 **Escalade COO — {agent_name}**\n"
        f"Tâche `{task_id}` a échoué après **{effective_max} tentatives**.\n"
        f"Dernière erreur : `{classify_error(last_exception)}`: "
        f"{str(last_exception)[:200]}\n"
        f"⚙️ Intervention humaine requise."
    )

    if telegram_notify_fn:
        telegram_notify_fn(escalation_msg)

    learn_from_failure(
        agent_id=canonical_agent,
        task=task_context or str(task_id or agent_name),
        error=str(last_exception)[:500],
    )

    logger.error("[RetryLoop] Escalation: %s", escalation_msg)

    return {
        "success": False,
        "result": None,
        "attempts": effective_max,
        "error": str(last_exception),
        "escalated": True,
    }
