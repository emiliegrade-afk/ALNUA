#!/usr/bin/env python3
"""Cross-check agent_personas.py ROOMS vs web/src/lib/agent-bureau.ts expectations."""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from config.agent_personas import AGENT_PERSONAS, ROOMS, get_agents_in_room  # noqa: E402

BUREAU_TS = ROOT / "web" / "src" / "lib" / "agent-bureau.ts"

BUREAU_ROOMS = {
    "hub": "direction",
    "secretary": "secretary_office",
    "app": "app_office",
    "gaming": "gaming_studio",
    "robo": "hardware_workshop",
    "marketing": "comms_hub",
    "rd": "rnd_lab",
    "finances": "accounting_office",
    "analytics": "analytics_room",
}


def parse_ts_agents() -> dict[str, str]:
    text = BUREAU_TS.read_text(encoding="utf-8")
    # id + room pairs from BUREAU_AGENTS entries
    pattern = re.compile(r'id:\s*"([^"]+)".*?room:\s*"([^"]+)"', re.DOTALL)
    agents: dict[str, str] = {}
    for block in text.split("{")[1:]:
        m_id = re.search(r'id:\s*"([^"]+)"', block)
        m_room = re.search(r'room:\s*"([^"]+)"', block)
        if m_id and m_room:
            agents[m_id.group(1)] = m_room.group(1)
    return agents


def main() -> int:
    errors: list[str] = []

    for aid, persona in AGENT_PERSONAS.items():
        room = persona["room"]
        if room not in ROOMS:
            errors.append(f"Persona {aid}: unknown room {room!r}")
        elif aid not in ROOMS[room]["agents"]:
            errors.append(f"Persona {aid}: room {room!r} but missing from ROOMS list")

    for room_id, room in ROOMS.items():
        for aid in room["agents"]:
            persona = AGENT_PERSONAS.get(aid)
            if persona is None:
                errors.append(f"ROOMS[{room_id!r}] lists unknown agent {aid!r}")
            elif persona["room"] != room_id:
                errors.append(
                    f"ROOMS[{room_id!r}] has {aid} but persona.room={persona['room']!r}"
                )
        if get_agents_in_room(room_id) != room["agents"]:
            errors.append(f"get_agents_in_room({room_id!r}) mismatch")

    ts_agents = parse_ts_agents()
    for aid, room in ts_agents.items():
        persona = AGENT_PERSONAS.get(aid)
        if persona is None:
            errors.append(f"TS agent {aid!r} not in AGENT_PERSONAS")
        elif persona["room"] != room:
            errors.append(
                f"TS agent {aid!r} room={room!r} but persona.room={persona['room']!r}"
            )

    for aid, persona in AGENT_PERSONAS.items():
        if aid not in ts_agents:
            errors.append(f"Persona {aid!r} missing from agent-bureau.ts")

    for bureau, room in BUREAU_ROOMS.items():
        expected = ROOMS.get(room, {}).get("agents", [])
        ts_in_bureau = [a for a, r in ts_agents.items() if r == room]
        if sorted(ts_in_bureau) != sorted(expected):
            errors.append(
                f"Bureau {bureau!r} (room {room!r}): "
                f"TS={sorted(ts_in_bureau)} vs ROOMS={sorted(expected)}"
            )

    # Each agent exactly once in TS
    if len(ts_agents) != len(set(ts_agents)):
        errors.append("Duplicate agent ids in agent-bureau.ts")

    if errors:
        print("FAILED — agent routing verification")
        for e in errors:
            print(f"  - {e}")
        return 1

    summary = {
        "personas": len(AGENT_PERSONAS),
        "rooms": len(ROOMS),
        "bureaus": len(BUREAU_ROOMS),
        "ts_agents": len(ts_agents),
    }
    print("OK — agent routing verified")
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
