"""Config Spark — assistante desktop ALNUA (persona Nadia)."""

import os
from pathlib import Path

HUB_ROOT = Path(os.getenv("ALNUA_HUB_ROOT", r"C:\Dev\ALUNA_HUB"))

LLM_BACKEND = os.getenv("NADIA_LLM_BACKEND", "ollama")

GLM_API_KEY = os.getenv("GLM_API_KEY", "")
GLM_BASE_URL = "https://open.bigmodel.cn/api/paas/v4"
GLM_MODEL = "glm-4-plus"

OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "qwen2.5:7b-instruct-q4_K_M")

WHISPER_MODEL = "base"
WHISPER_LANGUAGE = "fr"

TTS_BACKEND = os.getenv("NADIA_TTS_BACKEND", "edge")
TTS_VOICE = os.getenv("NADIA_TTS_VOICE", "fr-FR-VivienneMultilingualNeural")
TTS_RATE = os.getenv("NADIA_TTS_RATE", "-8%")
TTS_PITCH = os.getenv("NADIA_TTS_PITCH", "+2Hz")
KOKORO_MODEL = "fr"

WAKE_WORD = "nadia"
WAKE_WORD_ENABLED = os.getenv("NADIA_WAKE_WORD", "0") == "1"

WINDOW_TITLE = "Spark"
WINDOW_WIDTH = 1280
WINDOW_HEIGHT = 820
PRODUCT_NAME = "Spark"
PRODUCT_TAGLINE = "ALNUA"
THEME_BG = "#0B0C0F"
THEME_SURFACE = "#12141A"
THEME_ACCENT = "#E09B6A"
THEME_TEXT = "#F5F2EA"
THEME_MUTED = "#8B909A"

SESSION_ID = "desktop"
