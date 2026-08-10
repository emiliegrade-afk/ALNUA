"""Pydantic Settings mixins — coding pipeline, Obsidian, and NWIRO."""

from __future__ import annotations

from pydantic import Field


class SettingsCodingMixin:
    coding_timeout_s: int = Field(
        default=3600,
        alias="CODING_TIMEOUT_S",
        ge=300,
        le=7200,
        description="Max seconds per Claude Code coding session",
    )
    coding_max_turns: int = Field(
        default=60,
        alias="CODING_MAX_TURNS",
        ge=10,
        le=150,
    )
    coding_max_parallel: int = Field(
        default=2,
        alias="CODING_MAX_PARALLEL",
        ge=1,
        le=8,
        description="Max concurrent agent-ready issues processed",
    )
    coding_auto_merge: bool = Field(
        default=False,
        alias="CODING_AUTO_MERGE",
        description="Auto-merge PR when QA tests pass (all repos)",
    )
    coding_academy_auto_merge: bool = Field(
        default=True,
        alias="CODING_ACADEMY_AUTO_MERGE",
        description="Auto-merge academy PRs to master after QA (hub stays manual unless CODING_AUTO_MERGE)",
    )
    coding_qa_required: bool = Field(
        default=True,
        alias="CODING_QA_REQUIRED",
        description="Block PR if tsc/pytest/empty-file checks fail",
    )
    coding_merge_base_branch: str = Field(
        default="staging",
        alias="CODING_MERGE_BASE_BRANCH",
        description="Base branch for auto-created PRs when auto-merge enabled",
    )
    coding_max_worktrees: int = Field(
        default=8,
        alias="CODING_MAX_WORKTREES",
        ge=1,
        le=16,
    )
    # Phase A isolation (DEC-022 / SPEC_AGENT_ISOLATION)
    isolation_enabled: bool = Field(
        default=True,
        alias="ISOLATION_ENABLED",
        description="Resource locks + execution slots for parallel agents",
    )
    isolation_max_global: int = Field(
        default=8,
        alias="ISOLATION_MAX_GLOBAL",
        ge=1,
        le=32,
        description="Max concurrent agent executions across the Hub",
    )
    isolation_max_per_repo: int = Field(
        default=2,
        alias="ISOLATION_MAX_PER_REPO",
        ge=1,
        le=16,
        description="Max concurrent executions per git repo (aligns with CODING_MAX_PARALLEL)",
    )
    isolation_max_per_agent: int = Field(
        default=1,
        alias="ISOLATION_MAX_PER_AGENT",
        ge=1,
        le=4,
        description="Max concurrent executions per agent_id",
    )
    isolation_lock_ttl_s: int = Field(
        default=3600,
        alias="ISOLATION_LOCK_TTL_S",
        ge=60,
        le=86400,
    )
    isolation_wait_s: float = Field(
        default=30.0,
        alias="ISOLATION_WAIT_S",
        ge=0.0,
        le=600.0,
        description="Seconds to wait in queue for a lock/slot before fail-closed",
    )
    isolation_integrator_only_merge: bool = Field(
        default=True,
        alias="ISOLATION_INTEGRATOR_ONLY_MERGE",
        description="Only dev_integrator (and allowlisted system roles) merge protected branches",
    )
    isolation_fix_pipeline_merge: bool = Field(
        default=True,
        alias="ISOLATION_FIX_PIPELINE_MERGE",
        description="Allow fix_pipeline system role to merge main after QA+Spec (hotfix)",
    )
    coding_backend: str = Field(
        default="hub",
        alias="CODING_BACKEND",
        description="Coding executor: hub (Cursor-like), aider, or claude (CLI)",
    )
    aider_model: str = Field(
        default="",
        alias="AIDER_MODEL",
        description="Deprecated — coding uses Paramètres agent model. Fallback if set.",
    )
    github_repo_academy: str = Field(default="", alias="GITHUB_REPO_ACADEMY")
    repo_path_academy: str = Field(default="", alias="REPO_PATH_ACADEMY")
    nwiro_host: str = Field(default="localhost", alias="NWIRO_HOST")
    nwiro_port: int = Field(default=5353, alias="NWIRO_PORT", ge=1, le=65535)
    obsidian_vault_path: str = Field(
        default="",
        alias="OBSIDIAN_VAULT_PATH",
        description="Local Obsidian vault root (ex: D:\\ObsidianVault)",
    )
    obsidian_api_port: int = Field(
        default=27124,
        alias="OBSIDIAN_API_PORT",
        ge=1,
        le=65535,
        description="Obsidian Local REST API port (optional, phase 5)",
    )
    obsidian_api_key: str = Field(
        default="",
        alias="OBSIDIAN_API_KEY",
        description="Bearer token for Obsidian Local REST API",
    )
    obsidian_gaming_project_slug: str = Field(
        default="wyrdheim",
        alias="OBSIDIAN_GAMING_PROJECT_SLUG",
        description="Gaming project slug for GDD chunk sync",
    )
