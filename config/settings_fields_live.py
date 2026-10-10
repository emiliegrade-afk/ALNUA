"""Pydantic Settings mixin — Nadia Live (DEC-038 / DEC-039)."""

from __future__ import annotations

from pydantic import Field


class SettingsLiveMixin:
    live_task_max_concurrent: int = Field(
        default=3,
        alias="LIVE_TASK_MAX_CONCURRENT",
        ge=1,
        le=8,
        description="Tâches Jarvis Live exécutées en même temps (les autres restent queued)",
    )
    live_task_agents: str = Field(
        default="coo,secretary,plan",
        alias="LIVE_TASK_AGENTS",
        description="Allowlist CSV des exécutants Jarvis Live (coo, secretary, plan)",
    )
    live_voice_enabled: bool = Field(
        default=False,
        alias="LIVE_VOICE_ENABLED",
        description="Autorise POST /live/session (jeton éphémère OpenAI Realtime)",
    )
    openai_api_key: str = Field(
        default="",
        alias="OPENAI_API_KEY",
        description="Clé OpenAI, uniquement pour minter les jetons Realtime (jamais envoyée au navigateur)",
    )
    live_voice_model: str = Field(
        default="gpt-realtime",
        alias="LIVE_VOICE_MODEL",
        description="Modèle Realtime (relire la doc OpenAI : les noms évoluent)",
    )
    live_voice_max_minutes_per_day: int = Field(
        default=30,
        alias="LIVE_VOICE_MAX_MINUTES_PER_DAY",
        ge=1,
        le=600,
        description="Plafond quotidien de minutes de voix temps réel (au-delà : mode texte)",
    )
    live_voice_secret_ttl_seconds: int = Field(
        default=120,
        alias="LIVE_VOICE_SECRET_TTL_SECONDS",
        ge=10,
        le=600,
        description="Durée de vie du jeton éphémère avant connexion WebRTC",
    )
    live_pc_actions_enabled: bool = Field(
        default=False,
        alias="LIVE_PC_ACTIONS_ENABLED",
        description="Autorise open + écran + clic/frappe confirmés (DEC-039/044, jamais de shell libre)",
    )
    live_pc_allowed_domains: str = Field(
        default=(
            "instagram.com,mail.google.com,gmail.com,calendar.google.com,"
            "youtube.com,discord.com,github.com,notion.so,linkedin.com,"
            "wikipedia.org,google.com,facebook.com"
        ),
        alias="LIVE_PC_ALLOWED_DOMAINS",
        description="Domaines HTTPS autorisés pour open_url (CSV, suffixe inclus)",
    )
    live_pc_allowed_apps: str = Field(
        default=(
            "instagram=https://www.instagram.com,"
            "gmail=https://mail.google.com,"
            "calendar=https://calendar.google.com,"
            "youtube=https://www.youtube.com,"
            "discord=https://discord.com/app,"
            "github=https://github.com,"
            "notion=https://www.notion.so,"
            "linkedin=https://www.linkedin.com"
        ),
        alias="LIVE_PC_ALLOWED_APPS",
        description="Clés blanches nom->URL https ou chemin d'exécutable fixe (CSV)",
    )
    live_pc_allowed_dir: str = Field(
        default="",
        alias="LIVE_PC_ALLOWED_DIR",
        description="Dossier unique dans lequel open_file peut résoudre un chemin (vide = off)",
    )
    live_image_model: str = Field(
        default="google/gemini-2.5-flash-image",
        alias="LIVE_IMAGE_MODEL",
        description="Modèle OpenRouter Images pour « génère une image » (Lot 6)",
    )
