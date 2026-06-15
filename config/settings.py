from functools import lru_cache
from pathlib import Path
import logging

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

logger = logging.getLogger(__name__)

# Toujours charger .env a la racine du projet, quel que soit le cwd
_ENV_FILE = Path(__file__).resolve().parent.parent / ".env"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(_ENV_FILE),
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    supabase_url: str = Field(..., alias="SUPABASE_URL")
    supabase_key: str = Field(..., alias="SUPABASE_KEY")
    supabase_service_role_key: str = Field(
        default="",
        alias="SUPABASE_SERVICE_ROLE_KEY",
    )
    openrouter_api_key: str = Field(..., alias="OPENROUTER_API_KEY")
    composio_api_key: str = Field(default="", alias="COMPOSIO_API_KEY")
    discord_token: str = Field(default="", alias="DISCORD_TOKEN")
    discord_bot_token: str = Field(default="", alias="DISCORD_BOT_TOKEN")
    telegram_bot_token: str = Field(default="", alias="TELEGRAM_BOT_TOKEN")
    telegram_chat_id: str = Field(default="", alias="TELEGRAM_CHAT_ID")
    telegram_polling: bool = Field(
        default=False,
        alias="TELEGRAM_POLLING",
        description="Demarrer le bot Telegram en polling avec l'API (dev local)",
    )
    sentry_dsn: str = Field(default="", alias="SENTRY_DSN")
    sentry_webhook_secret: str = Field(default="", alias="SENTRY_WEBHOOK_SECRET")
    sentry_webhook_allow_unsigned: bool = Field(
        default=False,
        alias="SENTRY_WEBHOOK_ALLOW_UNSIGNED",
        description="Dev only — accept /webhook/sentry without HMAC when secret unset",
    )
    sentry_auto_issue: bool = Field(default=True, alias="SENTRY_AUTO_ISSUE")
    telegram_webhook_secret: str = Field(
        default="",
        alias="TELEGRAM_WEBHOOK_SECRET",
        description="Must match secret_token set via setWebhook (X-Telegram-Bot-Api-Secret-Token)",
    )

    openrouter_base_url: str = "https://openrouter.ai/api/v1"
    default_llm_model: str = "anthropic/claude-sonnet-4"
    api_host: str = "0.0.0.0"
    api_port: int = 8000
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
    github_repo_naia: str = Field(default="", alias="GITHUB_REPO_NAIA")
    github_repo_nomad: str = Field(default="", alias="GITHUB_REPO_NOMAD")
    hub_repo_path: str = Field(
        default="",
        alias="HUB_REPO_PATH",
    )
    repo_path_naia: str = Field(default="", alias="REPO_PATH_NAIA")
    repo_path_nomad: str = Field(default="", alias="REPO_PATH_NOMAD")
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

    creatorflow_app_url: str = Field(
        default="http://localhost:3002",
        alias="CREATORFLOW_APP_URL",
    )
    creatorflow_supabase_url: str = Field(
        default="",
        alias="CREATORFLOW_SUPABASE_URL",
    )
    creatorflow_supabase_service_role_key: str = Field(
        default="",
        alias="CREATORFLOW_SUPABASE_SERVICE_ROLE_KEY",
    )
    # CreatorFlow Studio — direct provider keys (server-side only)
    studio_google_api_key: str = Field(default="", alias="STUDIO_GOOGLE_API_KEY")
    studio_runway_api_key: str = Field(
        default="",
        alias="STUDIO_RUNWAY_API_KEY",
        description="Runway API secret (falls back to RUNWAYML_API_SECRET if empty)",
    )
    studio_elevenlabs_api_key: str = Field(default="", alias="STUDIO_ELEVENLABS_API_KEY")
    studio_elevenlabs_voice_id: str = Field(
        default="EXAVITQu4vr4xnSDxMaL",
        alias="STUDIO_ELEVENLABS_VOICE_ID",
        description="Default ElevenLabs voice id (Sarah)",
    )
    cf_export_mode: str = Field(default="auto", alias="CF_EXPORT_MODE")
    cf_export_daily_limit: int = Field(default=100, alias="CF_EXPORT_DAILY_LIMIT", ge=1)

    # Phase 0 — gradual migration flags (defaults preserve current behaviour)
    costs_unified_read: bool = Field(
        default=False,
        alias="COSTS_UNIFIED_READ",
        description="When true, all cost reads use cost_monitor JSON (Telegram included)",
    )
    costs_shadow_compare: bool = Field(
        default=True,
        alias="COSTS_SHADOW_COMPARE",
        description="Log deltas between cost_monitor and Supabase legacy reads",
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
    scheduler_timezone: str = Field(
        default="Europe/Paris",
        alias="SCHEDULER_TIMEZONE",
        description="IANA timezone for cron triggers (briefing, R&D, content sprint)",
    )

    # Autonomous coding pipeline (Super Plan Phase 1)
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
        description="Auto-merge academy PRs to master after QA (hub/NUAWAY stay manual)",
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

    @model_validator(mode="after")
    def _validate_security(self) -> "Settings":
        env = self.environment.strip().lower()
        is_prod = env in {"production", "prod", "staging"}

        if not self.hub_api_key.strip():
            if is_prod:
                raise ValueError(
                    "HUB_API_KEY is required when ENVIRONMENT is production/staging"
                )
            logger.warning(
                "HUB_API_KEY is unset — dev mode: API routes are open without X-Hub-Key. "
                "Set HUB_API_KEY in .env before exposing the server on a network."
            )

        if is_prod and not self.jwt_secret.strip():
            raise ValueError(
                "JWT_SECRET is required when ENVIRONMENT is production/staging"
            )

        if not self.hub_repo_path.strip():
            object.__setattr__(
                self,
                "hub_repo_path",
                str(Path(__file__).resolve().parent.parent),
            )

        if not self.discord_token.strip() and self.discord_bot_token.strip():
            object.__setattr__(self, "discord_token", self.discord_bot_token.strip())

        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
