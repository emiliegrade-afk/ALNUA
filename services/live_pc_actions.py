"""Nadia Live Lot 5 — named PC actions only (DEC-039).

Voice/agent text never becomes a shell command. It may only pick a whitelist
key or an https URL whose host is on LIVE_PC_ALLOWED_DOMAINS.
"""

from __future__ import annotations

import logging
import os
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlparse

from config.settings import get_settings

logger = logging.getLogger(__name__)

_KEY_RE = re.compile(r"^[a-z][a-z0-9_]{0,31}$")
_OPEN_RE = re.compile(
    r"\b(ouvre(?:-moi)?|ouvrir|open|lance|affiche|va sur)\b",
    re.IGNORECASE,
)
_URL_RE = re.compile(r"https?://[^\s)\]>'\"<>]+", re.IGNORECASE)


@dataclass(frozen=True)
class OpenRequest:
    kind: str  # url | app | file
    target: str
    key: str = ""


def wants_open(instruction: str) -> bool:
    """True only when the phrase is an open verb *and* the target is on the allowlist."""
    if not _OPEN_RE.search(instruction or ""):
        return False
    return parse_open(instruction) is not None


def maybe_open(instruction: str) -> str | None:
    """Run an open action, or None when the instruction is not an open request."""
    if not wants_open(instruction):
        return None
    return run_open(instruction)


def run_open(instruction: str) -> str:
    settings = get_settings()
    if not settings.live_pc_actions_enabled:
        return (
            "Je ne peux pas agir sur ce PC tant que LIVE_PC_ACTIONS_ENABLED n'est pas à 1. "
        )
    parsed = parse_open(instruction, settings)
    if parsed is None:
        keys = ", ".join(sorted(_app_map(settings)))
        return (
            "Je n'ouvre que ces pages : "
            f"{keys or '(liste vide)'}. "
            "Exemple : « ouvre Instagram » ou un lien https du même domaine."
        )
    if parsed.kind == "url":
        msg = _open_url(parsed.target)
    elif parsed.kind == "app":
        msg = _open_app(parsed.key, parsed.target)
    else:
        msg = _open_file(parsed.target, settings.live_pc_allowed_dir)
    from services.live_pc_display import parse_screen, wait_then_place

    screen = parse_screen(instruction)
    if screen is not None:
        placed = wait_then_place(screen, parsed.key)
        msg = f"{msg} {placed}"
    return msg


def parse_open(instruction: str, settings: object | None = None) -> OpenRequest | None:
    cfg = settings or get_settings()
    text = (instruction or "").strip()
    url_match = _URL_RE.search(text)
    if url_match:
        url = _normalize_https(url_match.group(0).rstrip(".,;\"'"))
        if url and _host_allowed(url, cfg.live_pc_allowed_domains):
            return OpenRequest(kind="url", target=url)
        return None
    apps = _app_map(cfg)
    lower = text.lower()
    for key in sorted(apps, key=len, reverse=True):
        if re.search(rf"\b{re.escape(key)}\b", lower):
            target = apps[key]
            kind = "url" if target.startswith("https://") else "app"
            return OpenRequest(kind=kind, target=target, key=key)
    return None


def _app_map(settings: object) -> dict[str, str]:
    raw = str(getattr(settings, "live_pc_allowed_apps", "") or "")
    out: dict[str, str] = {}
    for chunk in raw.split(","):
        if "=" not in chunk:
            continue
        key, value = chunk.split("=", 1)
        key, value = key.strip().lower(), value.strip()
        if not _KEY_RE.match(key) or not value:
            continue
        if value.startswith("https://"):
            url = _normalize_https(value)
            if url:
                out[key] = url
            continue
        path = Path(value)
        if path.is_absolute() and path.suffix.lower() in {".exe", ".bat", ".cmd"}:
            out[key] = str(path)
    return out


def _normalize_https(raw: str) -> str | None:
    parsed = urlparse(raw)
    if parsed.scheme.lower() != "https" or parsed.username or parsed.password:
        return None
    host = (parsed.hostname or "").lower().rstrip(".")
    if not host or parsed.port not in (None, 443):
        return None
    path = parsed.path or "/"
    query = f"?{parsed.query}" if parsed.query else ""
    return f"https://{host}{path}{query}"


def _host_allowed(url: str, domains_csv: str) -> bool:
    host = (urlparse(url).hostname or "").lower().rstrip(".")
    if not host:
        return False
    for domain in (d.strip().lower().lstrip(".") for d in domains_csv.split(",")):
        if not domain:
            continue
        if host == domain or host.endswith(f".{domain}"):
            return True
    return False


def _open_url(url: str) -> str:
    _launch_url(url)
    _log("open_url", url)
    return f"Page ouverte : {url}"


def _open_app(key: str, target: str) -> str:
    if target.startswith("https://"):
        return _open_url(target)
    path = Path(target)
    if not path.is_file():
        return f"L'app « {key} » n'est pas sur ce PC ({path.name})."
    subprocess.Popen([str(path)], shell=False)  # noqa: S603 — exact allowlist path
    _log("open_app", key)
    return f"App ouverte : {key}"


def _open_file(raw_path: str, allowed_dir: str) -> str:
    if not allowed_dir.strip():
        return "Aucun dossier fichier n'est autorisé (LIVE_PC_ALLOWED_DIR)."
    root = Path(allowed_dir).expanduser().resolve()
    candidate = Path(raw_path).expanduser().resolve()
    if not candidate.is_relative_to(root) or not candidate.is_file():
        return "Ce fichier est hors du dossier autorisé."
    os.startfile(str(candidate))  # noqa: S606 — Windows open, path already fenced
    _log("open_file", str(candidate))
    return f"Fichier ouvert : {candidate.name}"


def _launch_url(url: str) -> None:
    import webbrowser

    opened = webbrowser.open(url, new=2)
    if opened:
        return
    if os.name == "nt":
        os.startfile(url)  # noqa: S606 — https URL already validated
        return
    subprocess.Popen(["xdg-open", url], shell=False)  # noqa: S603


def _log(action: str, target: str) -> None:
    try:
        from agents.base import log_agent_action
        from database.supabase_client import get_supabase

        log_agent_action(
            get_supabase(),
            "secretary",
            action,
            input_summary=target[:120],
            output_summary="opened",
        )
    except Exception:
        logger.debug("live_pc log skipped", exc_info=True)
