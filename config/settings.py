from functools import lru_cache
from pathlib import Path
import logging

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from config.settings_fields_coding import SettingsCodingMixin
from config.settings_fields_comms import SettingsCommsMixin
from config.settings_fields_data import SettingsDataMixin
from config.settings_fields_hub import SettingsHubMixin

logger = logging.getLogger(__name__)

# Toujours charger .env a la racine du projet, quel que soit le cwd
_ENV_FILE = Path(__file__).resolve().parent.parent / ".env"


class Settings(
    SettingsDataMixin,
    SettingsCommsMixin,
    SettingsHubMixin,
    SettingsCodingMixin,
    BaseSettings,
):
    model_config = SettingsConfigDict(
        env_file=str(_ENV_FILE),
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    @property
    def telegram_secretary_chat_id_effective(self) -> str:
        return self.telegram_secretary_chat_id.strip() or self.telegram_chat_id.strip()

    @model_validator(mode="after")
    def _validate_security(self) -> "Settings":
        env = self.environment.strip().lower()
        is_prod = env in {"production", "prod", "staging"}

        if not self.hub_api_key.strip():
            raise ValueError(
                "HUB_API_KEY is required in every environment — set it in .env "
                "(see .env.example). There is no open dev-mode bypass anymore "
                "(see DECISIONS.md / BUGS.md SEC-002)."
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

        base = self.openrouter_base_url.strip().rstrip("/")
        if base.endswith("/chat/completions"):
            base = base[: -len("/chat/completions")]
        object.__setattr__(self, "openrouter_base_url", base or "https://openrouter.ai/api/v1")

        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
