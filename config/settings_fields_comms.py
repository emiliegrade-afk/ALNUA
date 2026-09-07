"""Pydantic Settings mixins — comms, integrations, and webhooks."""

from __future__ import annotations

from pydantic import Field


class SettingsCommsMixin:
    ceo_gmail: str = Field(
        default="alnua.global@gmail.com",
        alias="CEO_GMAIL",
        description="Compte Gmail ALNUA à connecter via Composio (Nadia)",
    )
    revolut_access_token: str = Field(
        default="",
        alias="REVOLUT_ACCESS_TOKEN",
        description="Revolut Business API bearer token (Grow+) — lecture dépenses only",
    )
    revolut_api_base: str = Field(
        default="https://b2b.revolut.com/api/1.0",
        alias="REVOLUT_API_BASE",
        description="Revolut Business API base URL",
    )
    discord_token: str = Field(default="", alias="DISCORD_TOKEN")
    discord_bot_token: str = Field(default="", alias="DISCORD_BOT_TOKEN")
    discord_guild_id: str = Field(
        default="",
        alias="DISCORD_GUILD_ID",
        description="ID du serveur Discord Wyrdheim — nécessaire pour le nombre de membres (Phase 18, ROADMAP.md)",
    )
    steam_api_key: str = Field(
        default="",
        alias="STEAM_API_KEY",
        description="Clé Steam Web API (steamcommunity.com/dev/apikey) — Phase 18, ROADMAP.md",
    )
    steam_app_id: str = Field(
        default="",
        alias="STEAM_APP_ID",
        description="App ID Steam de Wyrdheim (une fois publié sur Steamworks) — Phase 18, ROADMAP.md",
    )
    telegram_bot_token: str = Field(default="", alias="TELEGRAM_BOT_TOKEN")
    telegram_chat_id: str = Field(default="", alias="TELEGRAM_CHAT_ID")
    telegram_secretary_bot_token: str = Field(
        default="",
        alias="TELEGRAM_SECRETARY_BOT_TOKEN",
        description="Bot Telegram dédié Nadia (secrétaire) — token @BotFather séparé",
    )
    telegram_secretary_chat_id: str = Field(
        default="",
        alias="TELEGRAM_SECRETARY_CHAT_ID",
        description="Chat ID pour briefs Nadia (sinon fallback TELEGRAM_CHAT_ID)",
    )
    telegram_secretary_polling: bool = Field(
        default=False,
        alias="TELEGRAM_SECRETARY_POLLING",
        description="Polling du bot Nadia avec l'API Hub (dev local)",
    )
    telegram_secretary_webhook_secret: str = Field(
        default="",
        alias="TELEGRAM_SECRETARY_WEBHOOK_SECRET",
        description="Secret webhook bot Nadia (prod)",
    )
    telegram_voice_replies: bool = Field(
        default=False,
        alias="TELEGRAM_VOICE_REPLIES",
        description="Nadia + Aria : note audio overlay (Phase 47). Off par défaut. Aria ne parle que alerte/action/décision.",
    )
    voice_overlay_llm: bool = Field(
        default=True,
        alias="VOICE_OVERLAY_LLM",
        description="2e passe LLM pour la réplique parlée. 0 = repli local (pas d'OpenRouter).",
    )
    elevenlabs_tts: bool = Field(
        default=False,
        alias="ELEVENLABS_TTS",
        description="Lot 5 : TTS overlay ElevenLabs. 0 = Edge. Jamais de clone Marvel.",
    )
    elevenlabs_api_key: str = Field(default="", alias="ELEVENLABS_API_KEY")
    elevenlabs_voice_nadia: str = Field(
        default="",
        alias="ELEVENLABS_VOICE_NADIA",
        description="Voice ID original Nadia (Voice Lab), pas un clone film.",
    )
    elevenlabs_voice_aria: str = Field(
        default="",
        alias="ELEVENLABS_VOICE_ARIA",
        description="Voice ID original Aria (Voice Lab), pas un clone film.",
    )
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
