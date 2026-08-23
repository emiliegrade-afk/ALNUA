"""Fallback LLM local (Ollama / OpenAI-compatible) quand OpenRouter n'a plus de crédit.

OpenRouter renvoie HTTP 402 quand le compte n'a plus de crédit. Ce module :
- détecte ce signal (402 ou marqueurs « insufficient credits » / « quota »),
- expose un client chat/completions OpenAI-compatible vers un serveur local
  (Ollama http://localhost:11434/v1 par défaut, aussi LM Studio / vLLM),
- fusionne la config runtime data/llm_connectivity.json par-dessus env/Settings.
"""

from __future__ import annotations

import json
import logging
import time
from typing import Any

import httpx

from config.paths import get_hub_repo_path

logger = logging.getLogger(__name__)

_CONFIG_FILE = get_hub_repo_path() / "data" / "llm_connectivity.json"
_LOCAL_LLM_TIMEOUT_S = 300.0

_CREDIT_MARKERS: tuple[str, ...] = (
    "insufficient credit",
    "insufficient balance",
    "out of credits",
    "no credits",
    "credit limit",
    "credits exhausted",
    "quota exceeded",
    "billing",
    "balance too low",
    "not enough credits",
)


def _load_file_config() -> dict[str, Any]:
    try:
        if _CONFIG_FILE.exists():
            data = json.loads(_CONFIG_FILE.read_text(encoding="utf-8"))
            if isinstance(data, dict):
                return data
    except Exception:
        pass
    return {}


def _save_file_config(config: dict[str, Any]) -> None:
    _CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
    _CONFIG_FILE.write_text(
        json.dumps(config, indent=2, ensure_ascii=False), encoding="utf-8"
    )


def get_local_llm_config() -> dict[str, Any]:
    """Config locale fusionnée : env/Settings ← data/llm_connectivity.json."""
    try:
        from config.settings import get_settings

        s = get_settings()
        base: dict[str, Any] = {
            "enabled": bool(getattr(s, "local_llm_enabled", False)),
            "fallback_on_credit": bool(getattr(s, "local_llm_fallback_on_credit", True)),
            "base_url": getattr(s, "local_llm_base_url", "http://localhost:11434/v1"),
            "model": getattr(s, "local_llm_model", "qwen2.5:7b-instruct-q4_K_M"),
            "api_key": getattr(s, "local_llm_api_key", ""),
        }
    except Exception:
        base = {}
    merged = dict(base)
    for key, value in _load_file_config().items():
        if value is not None:
            merged[key] = value
    return merged


def save_local_llm_config(
    config: dict[str, Any], *, api_key: str | None = None
) -> dict[str, Any]:
    """Persiste dans data/llm_connectivity.json. api_key=None = conserver l'existant."""
    current = _load_file_config()
    for key in ("enabled", "fallback_on_credit", "base_url", "model"):
        if key in config and config[key] is not None:
            current[key] = config[key]
    if api_key is not None:
        current["api_key"] = api_key
    _save_file_config(current)
    logger.info("local_llm: connectivité mise à jour")
    return current


def local_llm_available() -> bool:
    cfg = get_local_llm_config()
    return bool(cfg.get("enabled")) and bool((cfg.get("base_url") or "").strip())


def fallback_on_credit_enabled() -> bool:
    return bool(get_local_llm_config().get("fallback_on_credit", True))


def is_credit_exhausted(status_code: int, body_text: str = "") -> bool:
    if status_code == 402:
        return True
    text = (body_text or "").lower()
    return any(marker in text for marker in _CREDIT_MARKERS)


def _completions_url(base_url: str) -> str:
    base = (base_url or "").strip().rstrip("/")
    if base.endswith("/chat/completions"):
        return base
    return f"{base}/chat/completions"


def _content_to_text(content: Any) -> str:
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts: list[str] = []
        for block in content:
            if isinstance(block, dict) and isinstance(block.get("text"), str):
                parts.append(block["text"])
            elif isinstance(block, str):
                parts.append(block)
        return "\n".join(parts)
    if content is None:
        return ""
    return str(content)


def _clean_messages(payload: dict[str, Any]) -> list[dict[str, Any]]:
    """Convertit le payload OpenRouter (avec cache_control) en messages OpenAI purs."""
    cleaned: list[dict[str, Any]] = []
    for m in payload.get("messages", []):
        if not isinstance(m, dict):
            continue
        role = m.get("role")
        if role not in ("system", "user", "assistant"):
            continue
        cleaned.append({"role": role, "content": _content_to_text(m.get("content"))})
    return cleaned


def _headers(cfg: dict[str, Any]) -> dict[str, str]:
    headers = {"Content-Type": "application/json"}
    key = (cfg.get("api_key") or "").strip()
    if key:
        headers["Authorization"] = f"Bearer {key}"
    return headers


def _local_payload(payload: dict[str, Any], cfg: dict[str, Any]) -> dict[str, Any]:
    return {
        "model": (cfg.get("model") or "").strip(),
        "messages": _clean_messages(payload),
        "temperature": payload.get("temperature", 0.7),
        "max_tokens": payload.get("max_tokens", 4096),
        "stream": False,
    }


def _extract_content(data: dict[str, Any]) -> str:
    try:
        content = data["choices"][0]["message"]["content"]
        return content or ""
    except (KeyError, IndexError, TypeError):
        raise RuntimeError(f"Réponse locale inattendue : {str(data)[:300]}") from None


def complete_local_sync(payload: dict[str, Any]) -> str:
    cfg = get_local_llm_config()
    url = _completions_url(cfg.get("base_url", ""))
    body = _local_payload(payload, cfg)
    with httpx.Client(timeout=_LOCAL_LLM_TIMEOUT_S) as client:
        response = client.post(url, json=body, headers=_headers(cfg))
    response.raise_for_status()
    return _extract_content(response.json())


async def complete_local_async(payload: dict[str, Any]) -> str:
    cfg = get_local_llm_config()
    url = _completions_url(cfg.get("base_url", ""))
    body = _local_payload(payload, cfg)
    async with httpx.AsyncClient(timeout=_LOCAL_LLM_TIMEOUT_S) as client:
        response = await client.post(url, json=body, headers=_headers(cfg))
    response.raise_for_status()
    return _extract_content(response.json())


def ping_local_llm() -> dict[str, Any]:
    """Test léger de connectivité (max_tokens=1)."""
    cfg = get_local_llm_config()
    base_url = (cfg.get("base_url") or "").strip()
    if not base_url:
        return {"ok": False, "error": "URL locale non configurée"}
    body = {
        "model": (cfg.get("model") or "").strip(),
        "messages": [{"role": "user", "content": "ping"}],
        "max_tokens": 1,
        "stream": False,
    }
    start = time.perf_counter()
    try:
        with httpx.Client(timeout=15.0) as client:
            response = client.post(
                _completions_url(base_url), json=body, headers=_headers(cfg)
            )
        response.raise_for_status()
        return {"ok": True, "latency_ms": round((time.perf_counter() - start) * 1000)}
    except Exception as exc:
        return {"ok": False, "error": str(exc)[:300]}
