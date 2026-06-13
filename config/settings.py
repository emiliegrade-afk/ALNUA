from functools import lru_cache
from pathlib import Path

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# Toujours charger .env à la racine du projet, quel que soit le cwd
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
    sentry_dsn: str = Field(default="", alias="SENTRY_DSN")

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

    @model_validator(mode="after")
    def _validate_security(self) -> "Settings":
        env = self.environment.strip().lower()
        is_prod = env in {"production", "prod", "staging"}

        if not self.hub_api_key.strip():
            if is_prod:
                raise ValueError(
                    "HUB_API_KEY is required when ENVIRONMENT is production/staging"
                )
            raise ValueError(
                "HUB_API_KEY is missing — copy .env.example to .env and set a key"
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
