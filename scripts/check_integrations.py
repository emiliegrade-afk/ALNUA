"""Check external integrations used by agents."""

from __future__ import annotations

import os
import socket
import sys
from pathlib import Path

import httpx

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from skills.skill_composio import get_composio_tools


def main() -> None:
    print("=== Composio tools per agent ===")
    for agent in [
        "coo_agent",
        "pm_agent",
        "marketing_agent",
        "content_agent",
        "dev_app_agent",
        "game_director_agent",
        "qa_agent",
        "hardware_agent",
        "spec_agent",
    ]:
        try:
            tools = get_composio_tools(agent_name=agent, user_id="alnua_check")
            print(f"  {'OK' if tools else 'WARN':4} {agent}: {len(tools)} tool(s)")
        except Exception as exc:
            print(f"  FAIL {agent}: {exc}")

    print("\n=== External services ===")
    host = os.getenv("NWIRO_HOST", "localhost")
    port = int(os.getenv("NWIRO_PORT", "5353"))
    sock = socket.socket()
    sock.settimeout(2)
    try:
        sock.connect((host, port))
        print(f"  OK   Nwiro {host}:{port}")
    except OSError as exc:
        print(f"  WARN Nwiro {host}:{port} — {exc}")
    finally:
        sock.close()

    for label, url in [
        ("OpenHands", os.getenv("OPENHANDS_URL", "http://localhost:3001")),
        ("API Hub", "http://localhost:8000/health"),
    ]:
        try:
            resp = httpx.get(url, timeout=3)
            print(f"  OK   {label}: HTTP {resp.status_code}")
        except Exception as exc:
            print(f"  WARN {label}: {exc}")

    optional = {
        "DISCORD_TOKEN": os.getenv("DISCORD_TOKEN") or os.getenv("DISCORD_BOT_TOKEN"),
        "PI_HOST": os.getenv("PI_HOST"),
        "TELEGRAM_BOT_TOKEN": os.getenv("TELEGRAM_BOT_TOKEN"),
    }
    print("\n=== Optional env ===")
    for key, value in optional.items():
        print(f"  {'OK' if value else 'WARN':4} {key}: {'set' if value else 'missing'}")


if __name__ == "__main__":
    main()
