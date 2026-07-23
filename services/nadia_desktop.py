"""Nadia desktop companion — boot greeting + Hub bridge (Phase 1)."""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from typing import Any

import httpx

from config.paths import get_hub_repo_path

logger = logging.getLogger(__name__)

_STATE_PATH = get_hub_repo_path() / "data" / "nadia_desktop.json"


def _load_state() -> dict[str, Any]:
    try:
        if _STATE_PATH.exists():
            return json.loads(_STATE_PATH.read_text(encoding="utf-8"))
    except Exception as exc:
        logger.debug("nadia_desktop state load: %s", exc)
    return {}


def _save_state(data: dict[str, Any]) -> None:
    _STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    _STATE_PATH.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


def _hub_api_base() -> str:
    port_file = get_hub_repo_path() / "data" / "hub_active_port.txt"
    port = 8003
    try:
        if port_file.exists():
            port = int(port_file.read_text(encoding="utf-8").strip())
    except Exception:
        pass
    return f"http://127.0.0.1:{port}"


def probe_hub() -> dict[str, Any]:
    """Check local Hub API health."""
    base = _hub_api_base()
    try:
        with httpx.Client(timeout=8.0) as client:
            res = client.get(f"{base}/health")
            if res.status_code == 200 and res.json().get("service") == "alnua-hub":
                return {"online": True, "api_url": base}
    except Exception as exc:
        logger.debug("hub probe failed: %s", exc)
    return {"online": False, "api_url": base}


def _time_greeting() -> str:
    hour = datetime.now().hour
    if hour < 12:
        return "Bonjour Emilie"
    if hour < 18:
        return "Bon après-midi Emilie"
    return "Bonsoir Emilie"


def build_boot_greeting(*, hub_online: bool) -> str:
    """Short Nadia message when PC / Hub starts."""
    hello = _time_greeting()
    if hub_online:
        return (
            f"☀️ {hello}, c'est Nadia.\n\n"
            "Le Hub ALNUA est en ligne — je fais le lien entre ton PC, l'équipe et toi.\n"
            "Tu peux me parler ici, sur Telegram, ou me demander de transmettre à Aria.\n\n"
            "_Prochaine étape : voix et accueil automatique au démarrage Windows._"
        )
    return (
        f"☀️ {hello}, c'est Nadia.\n\n"
        "Le Hub n'est pas encore prêt — lance **Demarrer-Hub.bat** ou attends quelques secondes.\n"
        "Je reste ton point d'entrée dès que l'API répond."
    )


def register_pc_boot(*, source: str = "desktop") -> dict[str, Any]:
    """Called at Windows logon — records session + returns greeting."""
    hub = probe_hub()
    greeting = build_boot_greeting(hub_online=hub["online"])
    now = datetime.now(timezone.utc).isoformat()
    state = _load_state()
    state.update(
        {
            "last_boot_at": now,
            "last_boot_source": source,
            "last_hub_online": hub["online"],
            "boot_count": int(state.get("boot_count") or 0) + 1,
        }
    )
    _save_state(state)
    try:
        from agents.base import log_agent_action
        from database.supabase_client import get_supabase

        log_agent_action(
            get_supabase(),
            "secretary",
            "nadia_desktop_boot",
            input_summary=source,
            output_summary="online" if hub["online"] else "hub_offline",
        )
    except Exception:
        pass
    return {
        "greeting": greeting,
        "hub": hub,
        "boot_at": now,
        "boot_count": state["boot_count"],
    }


def desktop_status() -> dict[str, Any]:
    """Status for secretary UI / desktop companion."""
    hub = probe_hub()
    state = _load_state()
    return {
        "hub": hub,
        "last_boot_at": state.get("last_boot_at"),
        "boot_count": state.get("boot_count", 0),
        "greeting_preview": build_boot_greeting(hub_online=hub["online"]),
    }
