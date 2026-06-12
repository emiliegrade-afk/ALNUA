"""Verify all ALNUA Hub agents: imports, config, and lightweight smoke tests."""

from __future__ import annotations

import sys
import traceback
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

AGENTS = [
    ("COOAgent", "agents.coo_agent", "COOAgent"),
    ("PMAgent", "agents.pm_agent", "PMAgent"),
    ("QAAgent", "agents.qa_agent", "QAAgent"),
    ("ContentAgent", "agents.content_agent", "ContentAgent"),
    ("BrainstormAgent", "agents.brainstorm_agent", "BrainstormAgent"),
    ("SpecAgent", "agents.spec_agent", "SpecAgent"),
    ("GameDirectorAgent", "agents.game_director_agent", "GameDirectorAgent"),
    ("DevGamingAgent", "agents.dev_gaming_agent", "DevGamingAgent"),
    ("HardwareAgent", "agents.hardware_agent", "HardwareAgent"),
    ("EmbeddedDevAgent", "agents.embedded_dev_agent", "EmbeddedDevAgent"),
    ("MarketingAgent", "agents.marketing_agent", "MarketingAgent"),
    ("DevAppAgent", "agents.dev_app_agent", "DevAppAgent"),
]


def main() -> int:
    failures = 0

    print("=== 1. IMPORTS ===")
    for name, module, cls_name in AGENTS:
        try:
            mod = __import__(module, fromlist=[cls_name])
            cls = getattr(mod, cls_name)
            print(f"  OK  {name}")
        except Exception as exc:
            failures += 1
            print(f"  FAIL {name}: {exc}")

    print("\n=== 2. SETTINGS ===")
    try:
        from config.settings import get_settings

        s = get_settings()
        for key, ok in [
            ("SUPABASE_URL", bool(s.supabase_url)),
            ("SUPABASE_KEY", bool(s.supabase_key)),
            ("OPENROUTER_API_KEY", bool(s.openrouter_api_key)),
            ("GITHUB_TOKEN", bool(s.github_token)),
            ("COMPOSIO_API_KEY", bool(s.composio_api_key)),
        ]:
            status = "OK" if ok else "MISSING"
            print(f"  {status}  {key}")
            if not ok:
                failures += 1
        print(f"  INFO  default_llm_model={s.default_llm_model}")
        print(f"  INFO  agent_model={s.agent_model}")
    except Exception as exc:
        failures += 1
        print(f"  FAIL settings: {exc}")

    print("\n=== 3. SUPABASE ===")
    try:
        from database.supabase_client import get_supabase

        db = get_supabase()
        res = db.table("projects").select("id,name").limit(5).execute()
        print(f"  OK  {len(res.data)} project(s) reachable")
    except Exception as exc:
        failures += 1
        print(f"  FAIL supabase: {exc}")

    print("\n=== 4. OPENROUTER (LLMClient) ===")
    try:
        from agents.base import LLMClient

        reply = LLMClient().complete(
            "Reponds en un seul mot.",
            "Dis OK",
            max_tokens=16,
        )
        print(f"  OK  reply={reply.strip()[:40]}")
    except Exception as exc:
        failures += 1
        print(f"  FAIL openrouter: {exc}")

    print("\n=== 5. AGENT INIT ===")
    try:
        from agents.coo_agent import COOAgent
        from agents.pm_agent import PMAgent
        from agents.qa_agent import QAAgent
        from agents.content_agent import ContentAgent
        from agents.brainstorm_agent import BrainstormAgent
        from agents.spec_agent import SpecAgent
        from agents.dev_app_agent import DevAppAgent

        db = get_supabase()
        inits = [
            ("COOAgent", lambda: COOAgent(db)),
            ("PMAgent", lambda: PMAgent(db)),
            ("QAAgent", lambda: QAAgent(db)),
            ("ContentAgent", lambda: ContentAgent(db)),
            ("BrainstormAgent", lambda: BrainstormAgent(db)),
            ("SpecAgent", lambda: SpecAgent(db)),
            ("DevAppAgent", lambda: DevAppAgent()),
        ]
        for name, factory in inits:
            try:
                factory()
                print(f"  OK  {name} init")
            except Exception as exc:
                failures += 1
                print(f"  FAIL {name} init: {exc}")
    except Exception as exc:
        failures += 1
        print(f"  FAIL init block: {exc}")
        traceback.print_exc()

    print("\n=== 6. COO SMOKE (handle_instruction, no crew) ===")
    try:
        from agents.coo_agent import COOAgent

        coo = COOAgent()
        # Irreversible guard — no LLM call
        r = coo.handle_instruction("publie le post sur Naïa")
        if "confirm" in r.lower():
            print("  OK  guardrail irreversible")
        else:
            failures += 1
            print(f"  FAIL guardrail: {r[:80]}")
    except Exception as exc:
        failures += 1
        print(f"  FAIL coo smoke: {exc}")

    print("\n=== 7. ROUTING ===")
    try:
        from agents.coo_agent import route_to_agent

        cases = [
            ("optimise le blueprint UE5", "dev_gaming"),
            ("bom eve hardware", "hardware"),
            ("seo discord communauté", "marketing"),
        ]
        for instruction, expected in cases:
            agent, _ = route_to_agent(instruction)
            ok = agent == expected
            print(f"  {'OK' if ok else 'FAIL'}  '{instruction[:30]}' -> {agent} (expected {expected})")
            if not ok:
                failures += 1
    except Exception as exc:
        failures += 1
        print(f"  FAIL routing: {exc}")

    print("\n=== 8. OPTIONAL INTEGRATIONS ===")
    optional = []
    try:
        from skills.skill_composio import get_composio_tools

        tools = get_composio_tools(agent_name="coo_agent", user_id="alnua_coo")
        optional.append(("Composio tools", len(tools) > 0, f"{len(tools)} tools"))
    except Exception as exc:
        optional.append(("Composio tools", False, str(exc)[:80]))

    import os

    optional.append(("Discord", bool(os.getenv("DISCORD_TOKEN")), "token empty" if not os.getenv("DISCORD_TOKEN") else "configured"))
    optional.append(("PI_HOST (Eve SSH)", bool(os.getenv("PI_HOST")), "not set" if not os.getenv("PI_HOST") else "configured"))

    for name, ok, detail in optional:
        print(f"  {'OK' if ok else 'WARN'}  {name}: {detail}")

    print("\n" + "=" * 40)
    if failures:
        print(f"RESULT: {failures} failure(s)")
        return 1
    print("RESULT: All critical checks passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
