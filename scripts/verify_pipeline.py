"""Audit pipeline : tous les agents connectés et exécutables."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))


def main() -> int:
    from config.agent_personas import AGENT_PERSONAS
    from services.agent_pipeline_registry import (
        AGENT_CLASSES,
        PIPELINE_METHODS,
        audit_pipeline,
    )

    print("=" * 60)
    print("ALNUA — Audit pipeline agents")
    print("=" * 60)

    persona_ids = {
        k for k in AGENT_PERSONAS if k not in {
            "direction", "secretary_office", "app_office", "gaming_studio",
            "rnd_lab", "comms_hub", "hardware_workshop", "accounting_office",
            "analytics_room", "app", "gaming", "innovation", "business",
            "finance", "analytics", "robo",
        }
    }
    registry_ids = set(AGENT_CLASSES)
    missing_in_registry = sorted(persona_ids - registry_ids)
    extra_in_registry = sorted(registry_ids - persona_ids)

    print(f"\nPersonas agents : {len(persona_ids)}")
    print(f"Registry pipeline : {len(registry_ids)}")
    if missing_in_registry:
        print(f"  MANQUE dans registry : {missing_in_registry}")
    if extra_in_registry:
        print(f"  Extra registry (OK si R&D sub-agents) : {extra_in_registry}")

    report = audit_pipeline()
    s = report["summary"]
    print(f"\n--- Instanciation ({s['agents_ok']}/{s['agents_total']}) ---")
    for aid in sorted(report["agents_ok"]):
        methods = PIPELINE_METHODS.get(aid, [])
        print(f"  OK  {aid:20} pipeline: {len(methods)} methode(s)")

    for fail in report["agents_fail"]:
        print(f"  FAIL {fail['agent_id']}: {fail['error'][:120]}")

    print(f"\n--- Methodes pipeline ({s['methods_ok']}/{s['methods_total']}) ---")
    for fail in report["methods_fail"]:
        print(f"  FAIL {fail['agent_id']}.{fail['method']}: {fail['error'][:100]}")

    print("\n--- OpenRouter (smoke) ---")
    try:
        from agents.base import LLMClient

        reply = LLMClient().complete("Reponds OK.", "test", max_tokens=8)
        print(f"  OK  LLM: {reply.strip()[:30]}")
    except Exception as exc:
        print(f"  FAIL LLM: {exc}")
        s["all_connected"] = False

    print("\n--- API /agents/status ---")
    try:
        import os
        import requests
        from dotenv import load_dotenv

        load_dotenv(ROOT / ".env")
        key = os.getenv("HUB_API_KEY", "")
        r = requests.get(
            "http://127.0.0.1:8000/agents/status",
            headers={"X-Hub-Key": key},
            timeout=5,
        )
        if r.status_code == 200:
            agents = r.json().get("agents", {})
            print(f"  OK  {len(agents)} agents dans OpenRoom")
            missing_or = sorted(registry_ids - set(agents))
            if missing_or:
                print(f"  WARN OpenRoom manque: {missing_or}")
        else:
            print(f"  WARN API status {r.status_code} (hub down?)")
    except Exception as exc:
        print(f"  WARN API: {exc}")

    print("\n" + "=" * 60)
    if s["all_connected"] and not missing_in_registry:
        print("RESULT: Tous les agents sont connectes au pipeline.")
        return 0
    print("RESULT: Des corrections sont necessaires (voir FAIL ci-dessus).")
    return 1


if __name__ == "__main__":
    sys.exit(main())
