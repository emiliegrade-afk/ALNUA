"""AUTO = one OpenRouter slug per agent (CEO Paramètres), not one model per tier.

Pins restored from data/agent_models.json (2026-09, before the utility rewrite).
Agents the CEO had not set follow the same families (M3 / GLM 5.2 / R1 / Qwen Coder /
Gemma 26B / Haiku / V3.1). Paramètres still wins if the JSON is edited.
"""
from __future__ import annotations

# CEO Paramètres (exact slugs). Do not "improve" these without Emilie.
AGENT_ROLE_MODELS: dict[str, str] = {
    "coo": "google/gemma-4-31b-it",
    "spec": "google/gemma-4-31b-it",
    "qa": "qwen/qwen3-235b-a22b",
    "pm": "deepseek/deepseek-r1-0528",
    "secretary": "z-ai/glm-5.2",
    "dev_app": "minimax/minimax-m3",
    "dev_backend": "z-ai/glm-5.2",
    "dev_gaming": "qwen/qwen3-coder",
    "embedded_dev": "qwen/qwen3-coder",
    "coding_coach": "deepseek/deepseek-chat-v3.1",
    "game_director": "google/gemini-2.5-pro",
    "level_designer": "deepseek/deepseek-r1-0528",
    "brainstorm": "minimax/minimax-m3",
    "rnd_agent": "minimax/minimax-m3",
    "rnd_dossier": "google/gemini-2.5-pro",
    "rnd_ceo": "minimax/minimax-m3",
    "rnd_committee": "deepseek/deepseek-r1-0528",
    "rnd_social": "google/gemma-4-26b-a4b-it",
    "rnd_visual": "minimax/minimax-m3",
    "rnd_product": "deepseek/deepseek-r1-0528",
    "marketing": "minimax/minimax-m3",
    "content": "google/gemma-4-26b-a4b-it",
    "accounting": "anthropic/claude-haiku-4-5",
    "controller": "anthropic/claude-haiku-4-5",
    "analyst_business": "deepseek/deepseek-r1-0528",
    "analyst_data": "deepseek/deepseek-chat-v3.1",
    "hardware": "deepseek/deepseek-chat-v3.1",
    # Same families — not in the original JSON
    "security_sentinel": "anthropic/claude-haiku-4-5",
    "legal_counsel": "deepseek/deepseek-r1-0528",
    "housekeeper": "z-ai/glm-5.2",
    "ads": "minimax/minimax-m3",
    "dev_frontend": "google/gemma-4-31b-it",
    "dev_integrator": "qwen/qwen3-coder",
    "content_app": "google/gemma-4-26b-a4b-it",
    "content_gaming": "google/gemma-4-26b-a4b-it",
    "content_robo": "google/gemma-4-26b-a4b-it",
    "content_company": "google/gemma-4-26b-a4b-it",
    "brand": "google/gemma-4-26b-a4b-it",
    "ai_programmer": "qwen/qwen3-coder",
    "environment_artist": "minimax/minimax-m3",
    "technical_artist": "qwen/qwen3-coder",
    "narrative_designer": "google/gemma-4-26b-a4b-it",
    "vfx_artist": "minimax/minimax-m3",
    "sound_designer": "deepseek/deepseek-chat-v3.1",
    "qa_gaming": "qwen/qwen3-235b-a22b",
    "vision_ai": "google/gemini-2.5-pro",
    "electronics": "deepseek/deepseek-chat-v3.1",
    "firmware": "qwen/qwen3-coder",
    "mechanical": "deepseek/deepseek-chat-v3.1",
    "industrial_design": "minimax/minimax-m3",
    "qa_robot": "qwen/qwen3-235b-a22b",
    "safety": "deepseek/deepseek-r1-0528",
    "simulation": "deepseek/deepseek-r1-0528",
}

# Coding-pipeline agents (Hub Agent / Aider) — model still comes from AUTO/Paramètres.
CODE_UTILITY_AGENT_IDS: frozenset[str] = frozenset(
    {
        "dev_app",
        "dev_backend",
        "dev_frontend",
        "dev_integrator",
        "dev_gaming",
        "embedded_dev",
        "firmware",
        "ai_programmer",
        "technical_artist",
    }
)
