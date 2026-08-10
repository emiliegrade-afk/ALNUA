"""Pydantic Settings mixins — Hub API, product paths, and feature flags."""

from __future__ import annotations

from pydantic import Field


class SettingsHubMixin:
    openrouter_base_url: str = "https://openrouter.ai/api/v1"
    default_llm_model: str = "anthropic/claude-sonnet-4"
    api_host: str = "0.0.0.0"
    api_port: int = 8003
    beta_portal_base_url: str = Field(
        default="http://localhost:3000",
        alias="BETA_PORTAL_BASE_URL",
    )
    grounding_dino_config_path: str = Field(
        default="models/groundingdino/GroundingDINO_SwinT_OGC.py",
        alias="GROUNDING_DINO_CONFIG_PATH",
    )
    grounding_dino_weights_path: str = Field(
        default="models/groundingdino/groundingdino_swint_ogc.pth",
        alias="GROUNDING_DINO_WEIGHTS_PATH",
    )
    grounding_dino_device: str = Field(
        default="auto",
        alias="GROUNDING_DINO_DEVICE",
    )
    github_token: str = Field(default="", alias="GITHUB_TOKEN")
    github_repo: str = Field(default="", alias="GITHUB_REPO")
    hub_repo_path: str = Field(
        default="",
        alias="HUB_REPO_PATH",
    )
    test_command: str = Field(
        default="pytest tests/ -v --tb=short",
        alias="TEST_COMMAND",
    )
    agent_model: str = Field(
        default="",
        alias="AGENT_MODEL",
    )
    hub_api_key: str = Field(default="", alias="HUB_API_KEY")
    jwt_secret: str = Field(default="", alias="JWT_SECRET")
    environment: str = Field(default="development", alias="ENVIRONMENT")
    alnua_workspace: str = Field(
        default="",
        alias="ALNUA_WORKSPACE",
        description="Dossier disque pour livrables R&D poles (ex: C:\\Dev\\ALNUA)",
    )
    hermes_skills_root: str = Field(
        default="",
        alias="HERMES_SKILLS_ROOT",
        description="Chemin skills/ du clone Hermes (ex: C:\\Dev\\hermes-agent-main\\skills)",
    )
    costs_unified_read: bool = Field(
        default=True,
        alias="COSTS_UNIFIED_READ",
        description="When true, all cost reads use cost_monitor JSON (Telegram included)",
    )
    costs_shadow_compare: bool = Field(
        default=False,
        alias="COSTS_SHADOW_COMPARE",
        description="Log deltas between cost_monitor and Supabase legacy reads (off by default)",
    )
    briefing_coo_section_enabled: bool = Field(
        default=False,
        alias="BRIEFING_COO_SECTION_ENABLED",
        description="Show COO executive tab on /briefing",
    )
    briefing_unified_generate: bool = Field(
        default=False,
        alias="BRIEFING_UNIFIED_GENERATE",
        description="Manual briefing generate uses morning orchestration",
    )
    admin_costs_page_enabled: bool = Field(
        default=False,
        alias="ADMIN_COSTS_PAGE_ENABLED",
    )
    admin_events_page_enabled: bool = Field(
        default=False,
        alias="ADMIN_EVENTS_PAGE_ENABLED",
    )
    admin_ab_test_page_enabled: bool = Field(
        default=False,
        alias="ADMIN_AB_TEST_PAGE_ENABLED",
    )
    gdd_manager_enabled: bool = Field(
        default=False,
        alias="GDD_MANAGER_ENABLED",
        description="Register GDD manager router and endpoints",
    )
    scheduler_leader: bool = Field(
        default=True,
        alias="SCHEDULER_LEADER",
        description="When false, skip APScheduler cron jobs on this worker (multi-process deploys)",
    )
    hub_fast_start: bool = Field(
        default=True,
        alias="HUB_FAST_START",
        description="Defer heavy background jobs so /health is ready in seconds",
    )
    scheduler_timezone: str = Field(
        default="Europe/Paris",
        alias="SCHEDULER_TIMEZONE",
        description="IANA timezone for cron triggers (briefing, R&D, content sprint)",
    )
