"""Config Nadia Desktop — ajuste les chemins selon ton install."""

import os
from pathlib import Path

# ── Chemin vers le projet ALNUA Hub ──────────────────────────────────────────
# Modifie ce chemin selon où est ton Hub sur ton PC
HUB_ROOT = Path(os.getenv("ALNUA_HUB_ROOT", r"C:\Dev\ALUNA_HUB"))

# ── LLM ──────────────────────────────────────────────────────────────────────
# "ollama"    → utilise le LLMClient du Hub (recommandé, cohérent avec Nadia)
# "ollama" → fallback local si Hub déconnecté
# "glm"    → API GLM-5.2 directe (nécessite GLM_API_KEY)
LLM_BACKEND = os.getenv("NADIA_LLM_BACKEND", "ollama")

# GLM-5.2 via API Z.ai (optionnel)
GLM_API_KEY  = os.getenv("GLM_API_KEY", "")
GLM_BASE_URL = "https://open.bigmodel.cn/api/paas/v4"
GLM_MODEL    = "glm-4-plus"          # remplace par "glm-5" quand dispo en API

# Ollama fallback
OLLAMA_URL   = os.getenv("OLLAMA_URL", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "qwen2.5:7b-instruct-q4_K_M")

# ── Voix ─────────────────────────────────────────────────────────────────────
# STT
WHISPER_MODEL = "base"          # "base" rapide, "large-v3" meilleur (plus lent)
WHISPER_LANGUAGE = "fr"

# TTS — "kokoro" local ou "edge" (Microsoft, gratuit, FR très bon)
TTS_BACKEND = os.getenv("NADIA_TTS_BACKEND", "edge")
TTS_VOICE = os.getenv("NADIA_TTS_VOICE", "fr-FR-VivienneMultilingualNeural")
TTS_RATE = os.getenv("NADIA_TTS_RATE", "-8%")
TTS_PITCH = os.getenv("NADIA_TTS_PITCH", "+2Hz")
KOKORO_MODEL = "fr"  # si TTS_BACKEND = "kokoro"

# ── Wake word ────────────────────────────────────────────────────────────────
WAKE_WORD         = "nadia"
WAKE_WORD_ENABLED = os.getenv("NADIA_WAKE_WORD", "0") == "1"  # activer plus tard

# ── UI ───────────────────────────────────────────────────────────────────────
WINDOW_TITLE  = "Nadia — ALNUA"
WINDOW_WIDTH  = 420
WINDOW_HEIGHT = 680
THEME_BG      = "#0E1014"      # Obsidienne ALNUA
THEME_SURFACE = "#16181D"
THEME_ACCENT  = "#B87333"      # Or Rosé Cuivré
THEME_TEXT    = "#F5F2EA"      # Ivoire
THEME_MUTED   = "#A7ADB5"      # Titane

# ── Session ──────────────────────────────────────────────────────────────────
SESSION_ID = "desktop"         # pour isoler les drafts email du desktop vs Telegram
