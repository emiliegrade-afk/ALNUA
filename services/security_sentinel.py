"""Security Sentinel — Hub patrol (auth bursts, config holes, optional lockdown).

Sentry = crash / error monitoring for apps.
This module = intrusion / leak *hygiene* for the Hub itself (local or VPS).
"""

from __future__ import annotations

import json
import logging
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from config.settings import get_settings

logger = logging.getLogger(__name__)

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
AUTH_FAIL_FILE = DATA / "security_auth_failures.json"
LOCKDOWN_FILE = DATA / "security_lockdown.json"
LAST_PATROL_FILE = DATA / "security_patrol_last.json"

_AUTH_BURST_THRESHOLD = 40  # failures in rolling window
_AUTH_WINDOW_MIN = 60
_WEAK_KEY_MIN_LEN = 16


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _iso(dt: datetime | None = None) -> str:
    return (dt or _utc_now()).isoformat()


def record_auth_failure(*, kind: str = "hub_key", client_ip: str | None = None) -> None:
    """Append a failed auth attempt (called from middleware)."""
    DATA.mkdir(parents=True, exist_ok=True)
    entries: list[dict[str, Any]] = []
    if AUTH_FAIL_FILE.is_file():
        try:
            raw = json.loads(AUTH_FAIL_FILE.read_text(encoding="utf-8"))
            if isinstance(raw, list):
                entries = [e for e in raw if isinstance(e, dict)]
        except (OSError, json.JSONDecodeError):
            entries = []
    entries.append({"at": _iso(), "kind": kind, "ip": (client_ip or "")[:64]})
    # Keep last 500
    entries = entries[-500:]
    AUTH_FAIL_FILE.write_text(
        json.dumps(entries, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def _recent_auth_failures(minutes: int = _AUTH_WINDOW_MIN) -> list[dict[str, Any]]:
    if not AUTH_FAIL_FILE.is_file():
        return []
    try:
        raw = json.loads(AUTH_FAIL_FILE.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return []
    if not isinstance(raw, list):
        return []
    cutoff = _utc_now().timestamp() - minutes * 60
    out: list[dict[str, Any]] = []
    for e in raw:
        if not isinstance(e, dict):
            continue
        try:
            ts = datetime.fromisoformat(str(e.get("at", "")).replace("Z", "+00:00"))
            if ts.timestamp() >= cutoff:
                out.append(e)
        except ValueError:
            continue
    return out


def is_lockdown_active() -> bool:
    if not LOCKDOWN_FILE.is_file():
        return False
    try:
        data = json.loads(LOCKDOWN_FILE.read_text(encoding="utf-8"))
        return bool(data.get("active"))
    except (OSError, json.JSONDecodeError):
        return False


def set_lockdown(active: bool, *, reason: str = "") -> dict[str, Any]:
    DATA.mkdir(parents=True, exist_ok=True)
    payload = {
        "active": bool(active),
        "reason": (reason or "")[:300],
        "updated_at": _iso(),
    }
    LOCKDOWN_FILE.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return payload


def _env_tracked_by_git() -> bool | None:
    """True if .env is tracked; None if git unavailable."""
    try:
        r = subprocess.run(
            ["git", "ls-files", "--error-unmatch", ".env"],
            cwd=str(ROOT),
            capture_output=True,
            text=True,
            timeout=10,
        )
        return r.returncode == 0
    except (OSError, subprocess.TimeoutExpired):
        return None


def run_patrol(*, notify: bool = True, auto_lockdown: bool | None = None) -> dict[str, Any]:
    """Run one security patrol. Returns findings + optional actions taken."""
    settings = get_settings()
    env = (settings.environment or "").strip().lower()
    is_prod = env in {"production", "prod", "staging"}
    findings: list[dict[str, Any]] = []

    key = (settings.hub_api_key or "").strip()
    if len(key) < _WEAK_KEY_MIN_LEN:
        findings.append(
            {
                "id": "weak_hub_key",
                "severity": "high",
                "title": "HUB_API_KEY trop courte",
                "detail": f"Longueur {len(key)} < {_WEAK_KEY_MIN_LEN}. Utilise une clé longue aléatoire.",
            }
        )

    if is_prod and not (settings.hub_ip_allowlist or "").strip():
        findings.append(
            {
                "id": "prod_no_ip_allowlist",
                "severity": "medium",
                "title": "Pas d'allowlist IP en prod",
                "detail": "Définis HUB_IP_ALLOWLIST (VPN / localhost) avant exposition VPS.",
            }
        )

    if is_prod and not (getattr(settings, "telegram_webhook_secret", "") or "").strip():
        findings.append(
            {
                "id": "prod_no_telegram_secret",
                "severity": "medium",
                "title": "TELEGRAM_WEBHOOK_SECRET manquant en prod",
                "detail": "Les webhooks Telegram doivent être signés en production.",
            }
        )

    tracked = _env_tracked_by_git()
    if tracked is True:
        findings.append(
            {
                "id": "env_in_git",
                "severity": "critical",
                "title": ".env suivi par Git",
                "detail": "Risque de fuite de secrets. Retire .env du tracking immédiatement.",
            }
        )

    fails = _recent_auth_failures()
    if len(fails) >= _AUTH_BURST_THRESHOLD:
        findings.append(
            {
                "id": "auth_burst",
                "severity": "critical",
                "title": f"Rafale d'échecs d'auth ({len(fails)}/{_AUTH_WINDOW_MIN}min)",
                "detail": "Possible scan / intrusion. Vérifie les logs et active le lockdown si besoin.",
                "count": len(fails),
            }
        )

    if is_lockdown_active():
        findings.append(
            {
                "id": "lockdown_on",
                "severity": "info",
                "title": "Lockdown actif",
                "detail": "Seules les IP locales (127.0.0.1 / ::1) sont acceptées.",
            }
        )

    actions: list[str] = []
    do_auto = auto_lockdown
    if do_auto is None:
        do_auto = bool(getattr(settings, "security_auto_lockdown", False))
    critical = [f for f in findings if f.get("severity") == "critical" and f.get("id") != "lockdown_on"]
    if do_auto and critical and not is_lockdown_active():
        set_lockdown(True, reason=critical[0].get("title", "auto"))
        actions.append("lockdown_enabled")
        findings.append(
            {
                "id": "auto_lockdown",
                "severity": "high",
                "title": "Lockdown activé automatiquement",
                "detail": critical[0].get("title", ""),
            }
        )

    if notify and any(f.get("severity") in {"high", "critical"} for f in findings):
        try:
            from skills.skill_hub_notify import notify_hub

            lines = ["🛡️ Security Sentinel — patrouille"]
            for f in findings:
                if f.get("severity") in {"high", "critical"}:
                    lines.append(f"[{f['severity'].upper()}] {f['title']}")
            notify_hub("\n".join(lines)[:3500])
            actions.append("notified")
        except Exception as exc:
            logger.warning("sentinel notify failed: %s", exc)

    report = {
        "ok": not any(f.get("severity") in {"high", "critical"} for f in findings if f.get("id") != "lockdown_on"),
        "at": _iso(),
        "environment": env,
        "findings": findings,
        "actions": actions,
        "auth_failures_window": len(fails),
        "lockdown": is_lockdown_active(),
        "note": (
            "Sentry ≠ cette patrouille : Sentry = crashs apps. "
            "Sentinel = hygiène Hub (clés, IP, rafales auth, .env)."
        ),
    }
    DATA.mkdir(parents=True, exist_ok=True)
    LAST_PATROL_FILE.write_text(
        json.dumps(report, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return report


def last_patrol() -> dict[str, Any] | None:
    if not LAST_PATROL_FILE.is_file():
        return None
    try:
        data = json.loads(LAST_PATROL_FILE.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else None
    except (OSError, json.JSONDecodeError):
        return None
