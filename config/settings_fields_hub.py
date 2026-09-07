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
    hub_api_key_web: str = Field(default="", alias="HUB_API_KEY_WEB")
    hub_api_key_n8n: str = Field(default="", alias="HUB_API_KEY_N8N")
    hub_api_key_mcp: str = Field(default="", alias="HUB_API_KEY_MCP")
    hub_api_key_cursor: str = Field(default="", alias="HUB_API_KEY_CURSOR")
    hub_ip_allowlist: str = Field(
        default="",
        alias="HUB_IP_ALLOWLIST",
        description="Comma-separated client IPs; empty = allow all",
    )
    security_auto_lockdown: bool = Field(
        default=False,
        alias="SECURITY_AUTO_LOCKDOWN",
        description="Security Sentinel auto-enables localhost lockdown on critical findings",
    )
    housekeeper_roots: str = Field(
        default="",
        alias="HOUSEKEEPER_ROOTS",
        description="Semicolon-separated extra dirs for PC housekeeper (Desktop/Documents always included)",
    )
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
    idle_work_enabled: bool = Field(
        default=True,
        alias="IDLE_WORK_ENABLED",
        description="Phase 39 — schedule idle_plan_day / idle_drain (DEC-021)",
    )
    idle_drain_interval_min: int = Field(
        default=180,
        alias="IDLE_DRAIN_INTERVAL_MIN",
        description="Minutes between idle_drain jobs when IDLE_WORK_ENABLED",
    )
    idle_max_items_per_drain: int = Field(
        default=1,
        ge=1,
        le=3,
        alias="IDLE_MAX_ITEMS_PER_DRAIN",
    )
    idle_default_autonomy_level: int = Field(
        default=1,
        ge=0,
        le=3,
        alias="IDLE_DEFAULT_AUTONOMY_LEVEL",
        description="Phase 30 autonomy_level mapped to max idle L0–L2",
    )
    idle_daily_budget_usd: float = Field(
        default=10.0,
        alias="IDLE_DAILY_BUDGET_USD",
        description="Soft daily budget for cost_monitor idle gates (adaptive)",
    )
    idle_offline_mode: bool = Field(
        default=False,
        alias="IDLE_OFFLINE_MODE",
        description="Force L1 idle drafts without OpenRouter (templates / offline triage)",
    )
    lounge_model: str = Field(
        default="",
        alias="LOUNGE_MODEL",
        description=(
            "OpenRouter slug for Agent Lounge LLM (DEC-031). "
            "Empty = deepseek/deepseek-chat-v3.2 (CN cheap). "
            "Never the agent's métier model. Alternatives: z-ai/glm-4.5-air, "
            "minimax/minimax-m2.7."
        ),
    )
    # Phase C Loop Engine (DEC-024)
    loop_max_iterations: int = Field(
        default=3,
        alias="LOOP_MAX_ITERATIONS",
        ge=1,
        le=10,
        description="Default Loop Engine max iterations (align watchdog)",
    )
    loop_strict_max_iterations: int = Field(
        default=2,
        alias="LOOP_STRICT_MAX_ITERATIONS",
        ge=1,
        le=5,
        description="Stricter cap for destructive / merge-sensitive loops",
    )
    loop_retry_sleep_s: float = Field(
        default=0.0,
        alias="LOOP_RETRY_SLEEP_S",
        ge=0.0,
        le=60.0,
        description="Default sleep between loop iterations (fix_pipeline overrides)",
    )
    # Phase D Review Chain (DEC-025)
    review_chain_staging_trust_min: float = Field(
        default=0.70,
        alias="REVIEW_CHAIN_STAGING_TRUST_MIN",
        ge=0.0,
        le=1.0,
        description="Min producer trust for auto-merge into staging",
    )
    # Phase E PermissionGuard (DEC-026)
    permission_guard_enabled: bool = Field(
        default=True,
        alias="PERMISSION_GUARD_ENABLED",
        description="Fail-closed Capability Pack checks before sensitive side-effects",
    )
    permission_guard_mcp_enabled: bool = Field(
        default=True,
        alias="PERMISSION_GUARD_MCP_ENABLED",
        description="Enforce Capability Packs on MCP-identified HTTP calls (X-MCP-Agent)",
    )
    # Phase F Context Engine (DEC-027)
    context_engine_enabled: bool = Field(
        default=True,
        alias="CONTEXT_ENGINE_ENABLED",
        description="Compile L1–L4 stratified context into agent prompts",
    )
    collective_promote_min_agents: int = Field(
        default=3,
        alias="COLLECTIVE_PROMOTE_MIN_AGENTS",
        ge=2,
        le=20,
        description="Distinct agents in same room before promoting lesson to L2",
    )
    # Local LLM failover — fallback quand OpenRouter n'a plus de crédit (HTTP 402).
    local_llm_enabled: bool = Field(
        default=False,
        alias="LOCAL_LLM_ENABLED",
        description="Activer le fallback LLM local (Ollama / LM Studio / vLLM OpenAI-compatible)",
    )
    local_llm_fallback_on_credit: bool = Field(
        default=True,
        alias="LOCAL_LLM_FALLBACK_ON_CREDIT",
        description="Bascule automatique vers le LLM local si OpenRouter renvoie 402 (crédits épuisés)",
    )
    local_llm_base_url: str = Field(
        default="http://localhost:11434/v1",
        alias="LOCAL_LLM_BASE_URL",
        description="Base URL OpenAI-compatible (Ollama : http://localhost:11434/v1)",
    )
    local_llm_model: str = Field(
        default="qwen2.5:7b-instruct-q4_K_M",
        alias="LOCAL_LLM_MODEL",
        description="Nom du modèle local (tag Ollama, id LM Studio, etc.)",
    )
    local_llm_api_key: str = Field(
        default="",
        alias="LOCAL_LLM_API_KEY",
        description="Bearer token optionnel (vide pour Ollama)",
    )
