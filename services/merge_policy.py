"""Merge policy — Phase A integrator-only rule (DEC-022 / SPEC_AGENT_ISOLATION).

Protected branches (main/master/staging) may only be merged by allowlisted
actors. Executors open PRs; they do not push to protected tips.
"""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)

PROTECTED_BRANCHES = frozenset({"main", "master", "staging"})

# Explicit allowlist — never infer from "close enough" agent names.
_INTEGRATOR_AGENTS = frozenset({"dev_integrator"})
_SYSTEM_HOTFIX = frozenset({"fix_pipeline"})
_ACADEMY_AUTO = frozenset({"coding_pipeline", "gh_issues", "system"})


class MergeDeniedError(PermissionError):
    """Raised when an actor may not merge into the target branch."""


def _integrator_only_enabled() -> bool:
    try:
        from config.settings import get_settings

        return bool(getattr(get_settings(), "isolation_integrator_only_merge", True))
    except Exception:
        return True


def _fix_pipeline_merge_enabled() -> bool:
    try:
        from config.settings import get_settings

        return bool(getattr(get_settings(), "isolation_fix_pipeline_merge", True))
    except Exception:
        return True


def is_protected_branch(branch: str | None) -> bool:
    return (branch or "").strip().lower() in PROTECTED_BRANCHES


def can_merge(
    agent_id: str,
    target_branch: str,
    *,
    repo_slug: str | None = None,
) -> tuple[bool, str]:
    """Return (allowed, reason). Fail-closed on unknown actors for protected branches."""
    aid = (agent_id or "").strip().lower()
    branch = (target_branch or "").strip().lower()
    slug = (repo_slug or "").strip().lower()

    if not branch:
        return False, "missing_target_branch"

    if not is_protected_branch(branch):
        return True, "unprotected_branch"

    if not _integrator_only_enabled():
        return True, "integrator_only_disabled"

    if aid in _INTEGRATOR_AGENTS:
        return True, "dev_integrator"

    if aid in _SYSTEM_HOTFIX:
        if _fix_pipeline_merge_enabled():
            return True, "fix_pipeline_hotfix"
        return False, "fix_pipeline_merge_disabled"

    if aid in _ACADEMY_AUTO and slug == "academy":
        return True, "academy_auto_merge"

    # Global CODING_AUTO_MERGE: system may merge staging only (never main/master).
    if aid in _ACADEMY_AUTO and branch == "staging":
        try:
            from config.settings import get_settings

            if bool(getattr(get_settings(), "coding_auto_merge", False)):
                return True, "coding_auto_merge_staging"
        except Exception:
            pass

    return False, f"denied:{aid or 'unknown'}->{branch}"


def assert_can_merge(
    agent_id: str,
    target_branch: str,
    *,
    repo_slug: str | None = None,
    human_approved: bool = False,
) -> None:
    ok, reason = can_merge(agent_id, target_branch, repo_slug=repo_slug)
    if not ok:
        raise MergeDeniedError(
            f"Merge denied for agent={agent_id!r} → {target_branch!r} "
            f"(repo={repo_slug or '-'}, reason={reason})"
        )
    # Phase E — Capability Pack fail-closed (DEC-026).
    # human_approved: CEO/humain autorise l'acteur allowlisté sans pack merge:main.
    if not human_approved:
        try:
            from services.permission_guard import (
                PermissionDeniedError,
                merge_capability_for_branch,
                require_capability,
            )

            cap = merge_capability_for_branch(target_branch)
            if cap:
                require_capability(
                    agent_id,
                    cap,
                    resource=f"branch:{target_branch}",
                    meta={"repo_slug": repo_slug, "source": "merge_policy"},
                )
        except PermissionDeniedError as exc:
            raise MergeDeniedError(str(exc)) from exc
    logger.debug(
        "merge_policy: allow %s → %s (%s)",
        agent_id,
        target_branch,
        reason,
    )


def merge_gate_summary(
    agent_id: str,
    target_branch: str,
    *,
    repo_slug: str | None = None,
) -> dict[str, Any]:
    ok, reason = can_merge(agent_id, target_branch, repo_slug=repo_slug)
    return {
        "allowed": ok,
        "reason": reason,
        "agent_id": agent_id,
        "target_branch": target_branch,
        "repo_slug": repo_slug,
        "protected": is_protected_branch(target_branch),
        "integrator_only": _integrator_only_enabled(),
    }


_HUMAN_DEPARTMENTS = frozenset({"ads", "finances", "finance", "publish", "marketing_paid"})


def _staging_trust_min() -> float:
    try:
        from config.settings import get_settings

        return float(getattr(get_settings(), "review_chain_staging_trust_min", 0.70))
    except Exception:
        return 0.70


def _producer_trust_score(producer_agent_id: str | None) -> float | None:
    if not producer_agent_id:
        return None
    try:
        from services.agent_trust import get_trust

        row = get_trust(producer_agent_id)
        return float(row.get("score", 0.7))
    except Exception:
        return None


def merge_autonomy(
    target_branch: str,
    *,
    repo_slug: str | None = None,
    department: str | None = None,
    producer_agent_id: str | None = None,
    actor_agent_id: str | None = None,
    human_approved: bool = False,
) -> dict[str, Any]:
    """Decide auto vs human for a merge *target* (DEC-025). Actor allowlist is separate."""
    branch = (target_branch or "").strip().lower()
    slug = (repo_slug or "").strip().lower()
    dept = (department or "").strip().lower()
    actor = (actor_agent_id or "").strip().lower()
    trust = _producer_trust_score(producer_agent_id)
    thr = _staging_trust_min()

    if human_approved:
        return {
            "mode": "auto",
            "reason": "human_approved",
            "trust": trust,
            "threshold": thr,
        }

    # System hotfix path (still gated by can_merge / assert_can_merge).
    if actor in _SYSTEM_HOTFIX and branch in {"main", "master"} and _fix_pipeline_merge_enabled():
        return {
            "mode": "auto",
            "reason": "fix_pipeline_hotfix",
            "trust": trust,
            "threshold": thr,
        }

    if dept in _HUMAN_DEPARTMENTS:
        return {
            "mode": "human_required",
            "reason": f"department:{dept}",
            "trust": trust,
            "threshold": thr,
        }

    if slug in {"academy", "lab"} or branch.startswith("lab/"):
        return {
            "mode": "auto",
            "reason": "academy_or_lab",
            "trust": trust,
            "threshold": thr,
        }

    if branch in {"main", "master"}:
        return {
            "mode": "human_required",
            "reason": "protected_main",
            "trust": trust,
            "threshold": thr,
        }

    if branch == "staging":
        if trust is None:
            trust = 0.7  # provisional default matches agent_trust
        if trust >= thr:
            return {
                "mode": "auto",
                "reason": f"staging_trust_ok:{trust:.2f}>={thr:.2f}",
                "trust": trust,
                "threshold": thr,
            }
        return {
            "mode": "human_required",
            "reason": f"staging_trust_low:{trust:.2f}<{thr:.2f}",
            "trust": trust,
            "threshold": thr,
        }

    if not is_protected_branch(branch):
        return {
            "mode": "auto",
            "reason": "unprotected_branch",
            "trust": trust,
            "threshold": thr,
        }

    return {
        "mode": "human_required",
        "reason": f"protected:{branch}",
        "trust": trust,
        "threshold": thr,
    }
