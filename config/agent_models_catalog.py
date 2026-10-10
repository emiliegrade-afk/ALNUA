"""OpenRouter model catalogue and UI category inference."""
from __future__ import annotations

# ---------------------------------------------------------------------------
# Catalogue de modèles disponibles
# ---------------------------------------------------------------------------

AVAILABLE_MODELS: dict[str, dict[str, str]] = {
    # ── Premium occidental — Claude Sonnet / Opus / Fable ─────────────────
    "anthropic/claude-sonnet-4":        {"label": "Claude Sonnet 4",        "tier": "premium", "region": "west"},
    "anthropic/claude-sonnet-4.5":      {"label": "Claude Sonnet 4.5",      "tier": "premium", "region": "west"},
    "anthropic/claude-sonnet-4.6":      {"label": "Claude Sonnet 4.6",      "tier": "premium", "region": "west"},
    "anthropic/claude-sonnet-5":        {"label": "Claude Sonnet 5",        "tier": "premium", "region": "west"},
    "anthropic/claude-opus-4":          {"label": "Claude Opus 4",          "tier": "premium", "region": "west"},
    "anthropic/claude-opus-4.1":        {"label": "Claude Opus 4.1",        "tier": "premium", "region": "west"},
    "anthropic/claude-opus-4.5":        {"label": "Claude Opus 4.5",        "tier": "premium", "region": "west"},
    "anthropic/claude-opus-4.6":        {"label": "Claude Opus 4.6",        "tier": "premium", "region": "west"},
    "anthropic/claude-opus-4.7":        {"label": "Claude Opus 4.7",        "tier": "premium", "region": "west"},
    "anthropic/claude-opus-4.8":        {"label": "Claude Opus 4.8",        "tier": "premium", "region": "west"},
    "anthropic/claude-opus-5":          {"label": "Claude Opus 5",          "tier": "premium", "region": "west", "category": "reasoning"},
    "anthropic/claude-fable-5":         {"label": "Claude Fable 5",         "tier": "premium", "region": "west"},
    "anthropic/claude-fable-5.1":       {"label": "Claude Fable 5.1",       "tier": "premium", "region": "west", "category": "reasoning"},
    # ── Premium occidental — GPT ───────────────────────────────────────────
    "openai/gpt-4o":                    {"label": "GPT-4o",                 "tier": "premium", "region": "west"},
    "openai/gpt-4-turbo":               {"label": "GPT-4 Turbo",            "tier": "premium", "region": "west"},
    "openai/gpt-5":                     {"label": "GPT-5",                  "tier": "premium", "region": "west"},
    "openai/gpt-5.1":                   {"label": "GPT-5.1",                "tier": "premium", "region": "west"},
    "openai/gpt-5.2":                   {"label": "GPT-5.2",                "tier": "premium", "region": "west"},
    "openai/gpt-5.4":                   {"label": "GPT-5.4",                "tier": "premium", "region": "west"},
    "openai/gpt-5.5":                   {"label": "GPT-5.5",                "tier": "premium", "region": "west"},
    "openai/gpt-5-pro":                 {"label": "GPT-5 Pro",              "tier": "premium", "region": "west"},
    "openai/gpt-5.4-pro":               {"label": "GPT-5.4 Pro",            "tier": "premium", "region": "west"},
    "openai/gpt-5.5-pro":               {"label": "GPT-5.5 Pro",            "tier": "premium", "region": "west"},
    "openai/gpt-5.6-sol":               {"label": "GPT-5.6 Sol",            "tier": "premium", "region": "west"},
    "openai/gpt-5.6-sol-pro":           {"label": "GPT-5.6 Sol Pro",        "tier": "premium", "region": "west", "category": "reasoning"},
    "openai/gpt-5.6-terra":             {"label": "GPT-5.6 Terra",          "tier": "standard", "region": "west"},
    "openai/gpt-5.6-terra-pro":         {"label": "GPT-5.6 Terra Pro",      "tier": "premium", "region": "west", "category": "reasoning"},
    "openai/gpt-5.6-luna":              {"label": "GPT-5.6 Luna",           "tier": "fast", "region": "west"},
    "openai/gpt-5.6-luna-pro":          {"label": "GPT-5.6 Luna Pro",       "tier": "standard", "region": "west"},
    # ── Premium occidental — autres ──────────────────────────────────────
    "google/gemini-2.5-pro":            {"label": "Gemini 2.5 Pro",         "tier": "premium", "region": "west"},
    "google/gemini-3.1-pro-preview":    {"label": "Gemini 3.1 Pro",         "tier": "premium", "region": "west"},
    "google/gemini-3.8-flash":          {"label": "Gemini 3.8 Flash",       "tier": "standard", "region": "west"},
    "google/gemini-3.5-flash":          {"label": "Gemini 3.5 Flash",       "tier": "standard", "region": "west"},
    "google/gemini-3.1-flash-lite":     {"label": "Gemini 3.1 Flash Lite",  "tier": "fast", "region": "west"},
    "google/gemma-4-31b-it":            {"label": "Gemma 4 31B",            "tier": "premium", "region": "west", "category": "code"},
    "google/gemma-4-26b-a4b-it":        {"label": "Gemma 4 26B A4B",        "tier": "standard", "region": "west", "category": "reasoning"},
    "x-ai/grok-4.3":                    {"label": "Grok 4.3",               "tier": "premium", "region": "west"},
    "x-ai/grok-4.5":                    {"label": "Grok 4.5",               "tier": "premium", "region": "west"},
    "x-ai/grok-4.6":                    {"label": "Grok 4.6",               "tier": "premium", "region": "west"},
    "x-ai/grok-4.20":                   {"label": "Grok 4.20",              "tier": "premium", "region": "west"},
    # ── Premium Chine — raisonnement profond, agents ───────────────────────
    "deepseek/deepseek-r1-0528":        {"label": "DeepSeek R1 0528",       "tier": "premium", "region": "cn"},
    "moonshotai/kimi-k2.5":             {"label": "Kimi K2.5",              "tier": "premium", "region": "cn"},
    "moonshotai/kimi-k2.6":             {"label": "Kimi K2.6",              "tier": "premium", "region": "cn"},
    "moonshotai/kimi-k2.7-code":        {"label": "Kimi K2.7 Code",         "tier": "premium", "region": "cn"},
    "moonshotai/kimi-k2-thinking":      {"label": "Kimi K2 Thinking",       "tier": "premium", "region": "cn", "category": "reasoning"},
    "moonshotai/kimi-k3":               {"label": "Kimi K3",                "tier": "premium", "region": "cn", "category": "reasoning"},
    "z-ai/glm-4.6":                     {"label": "GLM 4.6",                "tier": "premium", "region": "cn"},
    "z-ai/glm-4.7":                     {"label": "GLM 4.7",                "tier": "standard", "region": "cn"},
    "z-ai/glm-5":                       {"label": "GLM 5",                  "tier": "premium", "region": "cn"},
    "z-ai/glm-5-turbo":                 {"label": "GLM 5 Turbo",            "tier": "standard", "region": "cn"},
    "z-ai/glm-5.1":                     {"label": "GLM 5.1",                "tier": "premium", "region": "cn"},
    "z-ai/glm-5.2":                     {"label": "GLM 5.2 (Z.ai)",         "tier": "premium", "region": "cn", "category": "reasoning"},
    "z-ai/glm-5.3":                     {"label": "GLM 5.3",                "tier": "premium", "region": "cn", "category": "reasoning"},
    "z-ai/glm-5.3-flash":               {"label": "GLM 5.3 Flash",          "tier": "fast", "region": "cn", "category": "fast"},
    "z-ai/glm-5v-turbo":                {"label": "GLM 5V Turbo",           "tier": "standard", "region": "cn"},
    # ── Premium occidental — Mistral & NVIDIA ─────────────────────────────
    "mistralai/mistral-large-2512":     {"label": "Mistral Large 3",        "tier": "premium", "region": "west"},
    "nvidia/nemotron-3-ultra-550b-a55b":{"label": "Nemotron 3 Ultra 550B","tier": "premium", "region": "west"},
    # ── Standard occidental — Claude rapide / GPT mid ─────────────────────
    "anthropic/claude-opus-4.6-fast":   {"label": "Claude Opus 4.6 Fast",   "tier": "standard", "region": "west"},
    "anthropic/claude-opus-4.7-fast":   {"label": "Claude Opus 4.7 Fast",   "tier": "standard", "region": "west"},
    "anthropic/claude-opus-4.8-fast":   {"label": "Claude Opus 4.8 Fast",   "tier": "standard", "region": "west"},
    "anthropic/claude-haiku-4-5":       {"label": "Claude Haiku 4.5",       "tier": "standard", "region": "west"},
    "anthropic/claude-haiku-4.5":       {"label": "Claude Haiku 4.5",       "tier": "standard", "region": "west"},
    "openai/gpt-4.1":                   {"label": "GPT-4.1",                "tier": "standard", "region": "west"},
    "openai/gpt-4o-mini":               {"label": "GPT-4o Mini",            "tier": "standard", "region": "west"},
    "openai/gpt-5-mini":                {"label": "GPT-5 Mini",             "tier": "standard", "region": "west"},
    "openai/gpt-5.1-codex":             {"label": "GPT-5.1 Codex",          "tier": "standard", "region": "west"},
    "openai/gpt-5.1-codex-max":         {"label": "GPT-5.1 Codex Max",      "tier": "standard", "region": "west", "category": "code"},
    "openai/gpt-5.1-codex-mini":        {"label": "GPT-5.1 Codex Mini",     "tier": "fast", "region": "west", "category": "code"},
    "openai/gpt-5.2-chat":              {"label": "GPT-5.2 Chat",           "tier": "standard", "region": "west"},
    "openai/gpt-5.2-codex":             {"label": "GPT-5.2 Codex",          "tier": "standard", "region": "west"},
    "openai/gpt-5.2-pro":               {"label": "GPT-5.2 Pro",            "tier": "premium", "region": "west", "category": "reasoning"},
    "openai/gpt-5.3-codex":             {"label": "GPT-5.3 Codex",          "tier": "standard", "region": "west"},
    "openai/gpt-5.4-mini":              {"label": "GPT-5.4 Mini",           "tier": "standard", "region": "west"},
    "google/gemini-2.0-flash-001":      {"label": "Gemini 2.0 Flash",       "tier": "standard", "region": "west"},
    "minimax/minimax-m1":               {"label": "MiniMax M1",             "tier": "standard", "region": "cn"},
    "minimax/minimax-m3":               {"label": "MiniMax 3 (M3)",         "tier": "premium", "region": "cn", "category": "reasoning"},
    # ── Standard occidental — Mistral & NVIDIA ─────────────────────────────
    "mistralai/mistral-medium-3-5":     {"label": "Mistral Medium 3.5",     "tier": "standard", "region": "west"},
    "mistralai/mistral-small-2603":     {"label": "Mistral Small 4",        "tier": "standard", "region": "west"},
    "mistralai/codestral-2508":         {"label": "Codestral 2508",         "tier": "standard", "region": "west"},
    "mistralai/devstral-2512":          {"label": "Devstral 2",             "tier": "standard", "region": "west"},
    "nvidia/nemotron-3-super-120b-a12b":{"label": "Nemotron 3 Super 120B","tier": "standard", "region": "west"},
    "nvidia/llama-3.3-nemotron-super-49b-v1.5": {"label": "Nemotron Super 49B", "tier": "standard", "region": "west"},
    # ── Standard Chine — code & agents ───────────────────────────────────
    "minimax/minimax-m2.7":             {"label": "MiniMax M2.7",           "tier": "standard", "region": "cn"},
    "minimax/minimax-m2.7-highspeed":   {"label": "MiniMax M2.7 Rapide",    "tier": "standard", "region": "cn"},
    "deepseek/deepseek-chat-v3.1":      {"label": "DeepSeek V3.1",          "tier": "standard", "region": "cn"},
    "deepseek/deepseek-chat-v3-0324":   {"label": "DeepSeek V3",            "tier": "standard", "region": "cn"},
    "deepseek/deepseek-v3.2":           {"label": "DeepSeek V3.2",          "tier": "standard", "region": "cn"},
    "deepseek/deepseek-v4-pro":         {"label": "DeepSeek V4 Pro",        "tier": "premium", "region": "cn", "category": "reasoning"},
    "deepseek/deepseek-v4-flash":       {"label": "DeepSeek V4 Flash",      "tier": "fast", "region": "cn"},
    "qwen/qwen3-coder":                 {"label": "Qwen3 Coder 480B",       "tier": "standard", "region": "cn"},
    "qwen/qwen3-235b-a22b":             {"label": "Qwen3 235B",             "tier": "standard", "region": "cn"},
    "z-ai/glm-4.5":                     {"label": "GLM 4.5",                "tier": "standard", "region": "cn"},
    "z-ai/glm-4.7-flash":               {"label": "GLM 4.7 Flash",          "tier": "fast", "region": "cn"},
    # ── Fast occidental ────────────────────────────────────────────────────
    "anthropic/claude-haiku-3-5":       {"label": "Claude Haiku 3.5",       "tier": "fast", "region": "west"},
    "openai/gpt-4.1-nano":              {"label": "GPT-4.1 Nano",           "tier": "fast", "region": "west"},
    "openai/gpt-4.1-mini":              {"label": "GPT-4.1 Mini",           "tier": "fast", "region": "west"},
    "openai/gpt-5-nano":                {"label": "GPT-5 Nano",             "tier": "fast", "region": "west"},
    "openai/gpt-5.4-nano":              {"label": "GPT-5.4 Nano",           "tier": "fast", "region": "west"},
    "google/gemini-2.0-flash-lite-001": {"label": "Gemini 2.0 Flash Lite",  "tier": "fast", "region": "west"},
    "meta-llama/llama-3.3-70b-instruct":{"label": "Llama 3.3 70B",         "tier": "fast", "region": "west"},
    "nvidia/nemotron-3-nano-30b-a3b":   {"label": "Nemotron 3 Nano 30B",  "tier": "fast", "region": "west"},
    "mistralai/ministral-3b-2512":      {"label": "Ministral 3 3B",         "tier": "fast", "region": "west"},
    # ── Fast Chine ─────────────────────────────────────────────────────────
    "deepseek/deepseek-r1-0528-qwen3-8b": {"label": "DeepSeek R1 × Qwen3 8B", "tier": "fast", "region": "cn"},
    "z-ai/glm-4.5-air":                 {"label": "GLM 4.5 Air",            "tier": "fast", "region": "cn"},
    # ── Non censuré (OpenRouter — créatif, peu de refus) ───────────────────
    "x-ai/grok-3":                      {"label": "Grok 3",                   "tier": "premium", "region": "west", "category": "uncensored"},
    "x-ai/grok-3-mini":                 {"label": "Grok 3 Mini",              "tier": "standard", "region": "west", "category": "uncensored"},
    "cognitivecomputations/dolphin-mistral-24b-venice-edition": {
        "label": "Dolphin Mistral 24B Venice", "tier": "standard", "region": "west", "category": "uncensored",
    },
    "cognitivecomputations/dolphin3.0-r1-mistral-24b": {
        "label": "Dolphin 3.0 R1 Mistral", "tier": "premium", "region": "west", "category": "uncensored",
    },
    "nousresearch/deephermes-3-mistral-24b-preview": {
        "label": "DeepHermes 3 Mistral 24B", "tier": "standard", "region": "west", "category": "uncensored",
    },
    "nousresearch/deephermes-3-llama-3-8b-preview": {
        "label": "DeepHermes 3 Llama 8B", "tier": "fast", "region": "west", "category": "uncensored",
    },
    "gryphe/mythomax-l2-13b":           {"label": "MythoMax L2 13B",          "tier": "fast", "region": "west", "category": "uncensored"},
    "sao10k/l3.1-euryale-70b":          {"label": "Euryale 70B",              "tier": "standard", "region": "west", "category": "uncensored"},
    "undi95/toppy-m-7b":                {"label": "Toppy M 7B",               "tier": "fast", "region": "west", "category": "uncensored"},
    "mistralai/mistral-nemo":           {"label": "Mistral Nemo (souple)",    "tier": "fast", "region": "west", "category": "uncensored"},
}

MODEL_CATEGORIES: dict[str, str] = {
    "reasoning": "Raisonnement",
    "code": "Code",
    "chat": "Chat & rédaction",
    "fast": "Rapide & économique",
    "uncensored": "Non censuré",
}

MODEL_CATEGORY_ORDER: list[str] = [
    "reasoning",
    "code",
    "chat",
    "fast",
    "uncensored",
]


def _infer_model_category(model_id: str, meta: dict[str, str]) -> str:
    """Classe un modèle par usage (code, chat, reasoning…) — pas par région."""
    if meta.get("category"):
        return meta["category"]
    mid = model_id.lower()
    uncensored_markers = (
        "dolphin", "mythomax", "euryale", "toppy", "venice", "deephermes",
        "grok", "mistral-nemo", "uncensored",
    )
    if any(m in mid for m in uncensored_markers):
        return "uncensored"
    code_markers = ("codex", "coder", "codestral", "devstral", "k2.7-code", "k2.7 code", "gemma-4-31b")
    if any(m in mid for m in code_markers):
        return "code"
    reasoning_markers = (
        "r1", "opus", "fable",
        "gpt-5-pro", "gpt-5.4-pro", "gpt-5.5-pro", "gpt-5.6-sol", "gpt-5.6-terra-pro",
        "nemotron-3-ultra", "kimi-k2.6", "kimi-k3",
        "glm-5.1", "glm-5.2", "glm-5.3", "/glm-5",
        "minimax-m3", "gemma-4-26b", "gemini-3.1-pro",
    )
    if any(m in mid for m in reasoning_markers):
        return "reasoning"
    tier = meta.get("tier", "standard")
    if tier == "fast":
        return "fast"
    fast_markers = (
        "nano", "haiku", "flash-lite", "glm-4.5-air", "glm-5.3-flash",
        "glm-4.7-flash", "ministral", "3b-2512", "3b-", "gpt-5.6-luna",
    )
    if any(m in mid for m in fast_markers):
        return "fast"
    return "chat"


def get_enriched_available_models() -> dict[str, dict[str, str]]:
    """Catalogue modèles avec category pour l'UI Paramètres."""
    out: dict[str, dict[str, str]] = {}
    for model_id, meta in AVAILABLE_MODELS.items():
        enriched = dict(meta)
        enriched["category"] = _infer_model_category(model_id, meta)
        out[model_id] = enriched
    return out
