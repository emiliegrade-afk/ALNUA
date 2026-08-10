"""Autonomous coding pipeline configuration and helpers (Super Plan Phases 0–1)."""

from __future__ import annotations

import logging
import os
import re
import subprocess
from dataclasses import dataclass
from enum import StrEnum
from functools import lru_cache

logger = logging.getLogger(__name__)


class DevStack(StrEnum):
    PYTHON_FASTAPI = "python_fastapi"
    REACT_NATIVE_EXPO = "react_native_expo"
    NEXTJS = "nextjs"
    TYPESCRIPT = "typescript"


@dataclass(frozen=True)
class CodingPipelineConfig:
    timeout_s: int
    max_turns: int
    max_parallel: int
    auto_merge: bool
    academy_auto_merge: bool
    merge_base_branch: str
    max_worktrees: int
    backend: str
    aider_model: str
    qa_required: bool


@lru_cache
def get_coding_config() -> CodingPipelineConfig:
    """Read pipeline tuning from env (via settings when available)."""
    try:
        from config.settings import get_settings

        s = get_settings()
        return CodingPipelineConfig(
            timeout_s=s.coding_timeout_s,
            max_turns=s.coding_max_turns,
            max_parallel=s.coding_max_parallel,
            auto_merge=s.coding_auto_merge,
            academy_auto_merge=s.coding_academy_auto_merge,
            merge_base_branch=s.coding_merge_base_branch.strip(),
            max_worktrees=s.coding_max_worktrees,
            backend=s.coding_backend.strip().lower() or "hub",
            aider_model=(s.aider_model or "").strip(),
            qa_required=s.coding_qa_required,
        )
    except Exception:
        return CodingPipelineConfig(
            timeout_s=int(os.getenv("CODING_TIMEOUT_S", "3600")),
            max_turns=int(os.getenv("CODING_MAX_TURNS", "60")),
            max_parallel=int(os.getenv("CODING_MAX_PARALLEL", "2")),
            auto_merge=os.getenv("CODING_AUTO_MERGE", "false").lower() in ("1", "true", "yes"),
            academy_auto_merge=os.getenv("CODING_ACADEMY_AUTO_MERGE", "true").lower()
            in ("1", "true", "yes"),
            merge_base_branch=os.getenv("CODING_MERGE_BASE_BRANCH", "staging").strip(),
            max_worktrees=int(os.getenv("CODING_MAX_WORKTREES", "8")),
            backend=os.getenv("CODING_BACKEND", "hub").strip().lower(),
            aider_model=os.getenv("AIDER_MODEL", "").strip(),
            qa_required=os.getenv("CODING_QA_REQUIRED", "true").lower() in ("1", "true", "yes"),
        )


def branch_exists(repo_path: str, branch: str) -> bool:
    if not branch:
        return False
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--verify", f"refs/heads/{branch}"],
            cwd=repo_path,
            capture_output=True,
            text=True,
            timeout=15,
        )
        if result.returncode == 0:
            return True
        result = subprocess.run(
            ["git", "ls-remote", "--heads", "origin", branch],
            cwd=repo_path,
            capture_output=True,
            text=True,
            timeout=30,
        )
        return bool(result.stdout.strip())
    except Exception as exc:
        logger.debug("branch_exists(%s): %s", branch, exc)
        return False


def resolve_pr_base_branch(repo_path: str, config: CodingPipelineConfig | None = None) -> str | None:
    """PR target branch when auto-merge is enabled (staging preferred)."""
    cfg = config or get_coding_config()
    if not cfg.auto_merge:
        return None
    candidate = cfg.merge_base_branch
    if candidate and branch_exists(repo_path, candidate):
        return candidate
    logger.warning(
        "[CodingPipeline] Auto-merge activé mais branche '%s' absente sur %s",
        candidate,
        repo_path,
    )
    return None


def should_auto_merge_repo(repo_slug: str | None, config: CodingPipelineConfig | None = None) -> bool:
    """True when PRs for this repo should merge automatically after QA."""
    cfg = config or get_coding_config()
    if cfg.auto_merge:
        return True
    if (repo_slug or "").lower() == "academy" and cfg.academy_auto_merge:
        return True
    return False


def merge_pr_if_allowed(
    repo_path: str,
    pr_number: int,
    *,
    tests_passed: bool,
    repo_slug: str | None = None,
    config: CodingPipelineConfig | None = None,
    agent_id: str = "coding_pipeline",
    target_branch: str | None = None,
    producer_agent_id: str | None = None,
    department: str | None = None,
    human_approved: bool = False,
) -> dict[str, str | bool]:
    """Merge PR via gh CLI when auto-merge is on, QA passed, and merge policy allows."""
    cfg = config or get_coding_config()
    out: dict[str, str | bool] = {"merged": False, "reason": ""}

    if not should_auto_merge_repo(repo_slug, cfg):
        out["reason"] = "auto_merge_disabled"
        return out
    if not tests_passed:
        out["reason"] = "tests_failed"
        return out

    branch = (target_branch or cfg.merge_base_branch or resolve_default_branch(repo_path)).strip()
    try:
        from services.merge_policy import MergeDeniedError, assert_can_merge, merge_autonomy

        assert_can_merge(agent_id, branch, repo_slug=repo_slug)
        autonomy = merge_autonomy(
            branch,
            repo_slug=repo_slug,
            department=department,
            producer_agent_id=producer_agent_id or agent_id,
            actor_agent_id=agent_id,
            human_approved=human_approved,
        )
        if autonomy.get("mode") == "deny":
            out["reason"] = f"merge_autonomy:{autonomy.get('reason')}"
            return out
        if autonomy.get("mode") == "human_required":
            out["reason"] = f"human_required:{autonomy.get('reason')}"
            logger.info("[CodingPipeline] merge deferred (human): %s", autonomy.get("reason"))
            return out
    except MergeDeniedError as exc:
        out["reason"] = f"merge_policy:{exc}"
        logger.warning("[CodingPipeline] merge denied: %s", exc)
        return out

    try:
        from services.permission_guard import PermissionDeniedError, require_capability

        require_capability(
            agent_id,
            "github:pr:merge",
            resource=f"pr:{pr_number}",
            meta={"repo_slug": repo_slug, "target_branch": branch},
        )
    except PermissionDeniedError as exc:
        out["reason"] = f"capability:{exc}"
        logger.warning("[CodingPipeline] github:pr:merge denied: %s", exc)
        return out
    except Exception:
        pass

    try:
        result = subprocess.run(
            [
                "gh",
                "pr",
                "merge",
                str(pr_number),
                "--merge",
                "--delete-branch",
            ],
            cwd=repo_path,
            capture_output=True,
            text=True,
            timeout=120,
        )
        if result.returncode != 0:
            out["reason"] = (result.stderr or result.stdout or "gh pr merge failed")[:500]
            logger.warning("[CodingPipeline] gh pr merge #%s failed: %s", pr_number, out["reason"])
            return out
        out["merged"] = True
        out["reason"] = "merged"
        logger.info("[CodingPipeline] PR #%s merged (repo=%s)", pr_number, repo_slug or "?")
        subprocess.run(
            ["git", "pull", "origin", resolve_default_branch(repo_path)],
            cwd=repo_path,
            capture_output=True,
            text=True,
            timeout=60,
        )
        return out
    except Exception as exc:
        out["reason"] = str(exc)[:500]
        logger.error("[CodingPipeline] merge_pr_if_allowed: %s", exc)
        return out


def resolve_default_branch(repo_path: str) -> str:
    """Detect the repo's default branch (master/main) for diff/PR base."""
    for candidate in ("master", "main"):
        try:
            result = subprocess.run(
                ["git", "rev-parse", "--verify", candidate],
                cwd=repo_path,
                capture_output=True,
                text=True,
                timeout=15,
            )
            if result.returncode == 0:
                return candidate
        except Exception:
            continue
    return "main"


def parse_pr_number(pr_url: str | None) -> int | None:
    if not pr_url:
        return None
    match = re.search(r"/pull/(\d+)", pr_url)
    return int(match.group(1)) if match else None


from services.coding_pipeline_stack import (  # noqa: E402
    detect_stack,
    stack_expert_role,
    stack_rules_block,
)

__all__ = [
    "CodingPipelineConfig",
    "DevStack",
    "branch_exists",
    "detect_stack",
    "get_coding_config",
    "merge_pr_if_allowed",
    "parse_pr_number",
    "resolve_default_branch",
    "resolve_pr_base_branch",
    "should_auto_merge_repo",
    "stack_expert_role",
    "stack_rules_block",
]
