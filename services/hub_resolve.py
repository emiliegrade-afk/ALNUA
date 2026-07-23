"""Resolve live Hub API URL — avoids stale port 8000 when dev runs on 8003."""

from __future__ import annotations

import logging
import os
import time
from pathlib import Path
from typing import Any

import httpx

logger = logging.getLogger(__name__)

_CACHE: dict[str, Any] = {"url": None, "at": 0.0}
_TTL_S = 30.0
_DEFAULT_PORTS = (8003, 8002, 8000, 8001)
_ACTIVE_PORT_FILE = Path(__file__).resolve().parent.parent / "data" / "hub_active_port.txt"


def _read_active_port_file() -> int | None:
    try:
        if _ACTIVE_PORT_FILE.exists():
            return int(_ACTIVE_PORT_FILE.read_text(encoding="utf-8").strip())
    except (ValueError, OSError):
        pass
    return None


def _hub_responds(base: str) -> bool:
    """True when this instance runs orchestration (not a zombie /health-only process)."""
    try:
        with httpx.Client(timeout=2.5) as client:
            resp = client.get(f"{base}/orchestration/pipeline-status")
            return resp.status_code == 200
    except Exception:
        return False


def _candidate_ports() -> tuple[int, ...]:
    file_port = _read_active_port_file()
    if file_port is not None:
        ordered = [file_port]
        ordered.extend(p for p in _DEFAULT_PORTS if p != file_port)
        return tuple(ordered)
    return _DEFAULT_PORTS


def resolve_hub_api_url(*, force_refresh: bool = False) -> str:
    """
    Return configured HUB_API_URL or first port with a live pipeline-status endpoint.
    """
    configured = (
        os.getenv("HUB_API_URL", "").strip()
        or os.getenv("HUB_API_BACKEND_URL", "").strip()
    )
    if configured:
        return configured.rstrip("/")

    now = time.monotonic()
    if (
        not force_refresh
        and _CACHE.get("url")
        and now - float(_CACHE.get("at") or 0) < _TTL_S
    ):
        return str(_CACHE["url"])

    for port in _candidate_ports():
        base = f"http://127.0.0.1:{port}"
        if _hub_responds(base):
            _CACHE["url"] = base
            _CACHE["at"] = now
            if port != 8000:
                logger.info("[HubResolve] Hub actif sur port %s", port)
            return base

    fallback = "http://127.0.0.1:8000"
    _CACHE["url"] = fallback
    _CACHE["at"] = now
    return fallback