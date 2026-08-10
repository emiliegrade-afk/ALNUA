"""Pydantic Settings mixins — data stores, LLM, and rate limiting."""

from __future__ import annotations

from pydantic import Field


class SettingsDataMixin:
    supabase_url: str = Field(..., alias="SUPABASE_URL")
    supabase_key: str = Field(..., alias="SUPABASE_KEY")
    supabase_service_role_key: str = Field(
        default="",
        alias="SUPABASE_SERVICE_ROLE_KEY",
    )
    openrouter_api_key: str = Field(..., alias="OPENROUTER_API_KEY")
    composio_api_key: str = Field(default="", alias="COMPOSIO_API_KEY")
    composio_user_id: str = Field(
        default="alnua_coo",
        alias="COMPOSIO_USER_ID",
        description="Identité OAuth Composio (Gmail/Calendar CEO)",
    )
    default_tenant_id: str = Field(
        default="alnua_coo",
        alias="DEFAULT_TENANT_ID",
        description="Fallback tenant when X-Tenant-ID header is absent",
    )
    llm_cache_enabled: bool = Field(
        default=True,
        alias="LLM_CACHE_ENABLED",
        description="Cache deterministic LLM responses (temp <= 0.1)",
    )
    llm_cache_ttl_s: int = Field(
        default=3600,
        alias="LLM_CACHE_TTL_S",
        ge=60,
        le=86400,
    )
    openrouter_prompt_cache_enabled: bool = Field(
        default=True,
        alias="OPENROUTER_PROMPT_CACHE_ENABLED",
        description="Send cache_control + session_id so static system/tools are cached",
    )
    openrouter_prompt_cache_ttl: str = Field(
        default="1h",
        alias="OPENROUTER_PROMPT_CACHE_TTL",
        description="Ephemeral cache TTL for Anthropic-compatible breakpoints: 5m or 1h",
    )
    llm_http_timeout_s: float = Field(
        default=60.0,
        alias="LLM_HTTP_TIMEOUT_S",
        ge=10.0,
        le=300.0,
        description="OpenRouter HTTP timeout (seconds) — fail fast to avoid retry burn",
    )
    llm_http_timeout_long_s: float = Field(
        default=120.0,
        alias="LLM_HTTP_TIMEOUT_LONG_S",
        ge=30.0,
        le=600.0,
        description="Long OpenRouter timeout for coding / heavy generations",
    )
    llm_max_attempts_per_model: int = Field(
        default=2,
        alias="LLM_MAX_ATTEMPTS_PER_MODEL",
        ge=1,
        le=3,
        description="Retries per model before failover (cap 3)",
    )
    rate_limit_enabled: bool = Field(
        default=True,
        alias="RATE_LIMIT_ENABLED",
        description="Enable in-memory rate limiting on assistant/chat routes",
    )
    redis_url: str = Field(
        default="",
        alias="REDIS_URL",
        description="Redis URL for cache, rate limits, and RQ queue (redis://localhost:6379)",
    )
    backup_s3_bucket: str = Field(
        default="",
        alias="BACKUP_S3_BUCKET",
        description="S3 bucket for encrypted daily backups",
    )
    backup_s3_prefix: str = Field(
        default="alnua-hub/",
        alias="BACKUP_S3_PREFIX",
    )
    aws_access_key_id: str = Field(default="", alias="AWS_ACCESS_KEY_ID")
    aws_secret_access_key: str = Field(default="", alias="AWS_SECRET_ACCESS_KEY")
    aws_region: str = Field(default="eu-west-3", alias="AWS_REGION")
