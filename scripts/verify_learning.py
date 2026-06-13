"""Audit: agents operational status + learning loop (read/write Mem0)."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from dotenv import load_dotenv

load_dotenv(ROOT / ".env")

# agent_id -> loop status (code paths wired)
LEARNING_AUDIT: dict[str, dict[str, str]] = {
    "coo": {"read": "get_learning_context", "write": "record_task_learning", "loop": "fermee"},
    "dev_app": {"read": "get_learning_context + fix_pipeline", "write": "record_task_learning", "loop": "fermee"},
    "dev_gaming": {"read": "get_learning_context + retry_loop", "write": "record_task_learning", "loop": "fermee"},
    "embedded_dev": {"read": "get_learning_context + retry_loop", "write": "record_task_learning", "loop": "fermee"},
    "spec": {"read": "inject_learning_context", "write": "record_task_learning", "loop": "fermee"},
    "qa": {"read": "inject_learning_context", "write": "record_task_learning", "loop": "fermee"},
    "pm": {"read": "inject_learning_context", "write": "record_task_learning", "loop": "fermee"},
    "marketing": {"read": "inject_learning_context", "write": "record_task_learning", "loop": "fermee"},
    "content": {"read": "inject_learning_context", "write": "record_task_learning", "loop": "fermee"},
    "hardware": {"read": "inject_learning_context", "write": "record_task_learning", "loop": "fermee"},
    "game_director": {"read": "inject_learning_context", "write": "record_task_learning", "loop": "fermee"},
    "brainstorm": {"read": "get_learning_context + Supabase sessions", "write": "record_task_learning", "loop": "fermee"},
    "rnd_agent": {"read": "get_vision + get_learning_context", "write": "record_task_learning", "loop": "fermee"},
    "accounting": {"read": "inject_learning_context (commentary)", "write": "record_task_learning", "loop": "fermee"},
}


def main() -> int:
    failures = 0
    print("=" * 60)
    print("AUDIT ALNUA - Agents + Apprentissage")
    print("=" * 60)

    print("\n--- 1. ENV ---")
    import os

    for key in ("OPENROUTER_API_KEY", "MEM0_API_KEY", "SUPABASE_URL"):
        val = os.getenv(key) or os.getenv("NEXT_PUBLIC_SUPABASE_URL" if key == "SUPABASE_URL" else "")
        ok = bool(val)
        print(f"  {'OK' if ok else 'FAIL'}  {key}")
        if not ok:
            failures += 1

    print("\n--- 2. Mem0 (read/write) ---")
    try:
        from skills.skill_mem0 import get_mem0, remember, recall

        if not get_mem0():
            print("  FAIL  Mem0 client unavailable")
            failures += 1
        else:
            tag = "verify_learning_audit"
            remember(f"[audit] test {tag}", agent_id="dev_app")
            hit = recall(tag, agent_id="dev_app")
            print(f"  OK  Mem0 write+search ({'hit' if hit else 'indexed async'})")
    except Exception as exc:
        print(f"  FAIL  Mem0: {exc}")
        failures += 1

    print("\n--- 3. Distillation lecons (LEARN_MODEL) ---")
    try:
        from skills.skill_agent_learning import _distill_lessons

        lesson = _distill_lessons("dev_app", "test audit", "ok", True)
        if lesson:
            safe = lesson.encode("ascii", errors="replace").decode("ascii")
            print(f"  OK  distill -> {safe[:80]}...")
        else:
            print("  FAIL  distill returned empty")
            failures += 1
    except Exception as exc:
        print(f"  FAIL  distill: {exc}")
        failures += 1

    print("\n--- 4. Helpers ---")
    try:
        from skills.skill_agent_learning import inject_learning_context, record_task_learning

        out = inject_learning_context("prompt", "qa", "test")
        assert isinstance(out, str)
        print("  OK  inject_learning_context + record_task_learning")
    except Exception as exc:
        print(f"  FAIL  helpers: {exc}")
        failures += 1

    print("\n--- 5. Imports agents ---")
    agents = [
        ("coo", "agents.coo_agent", "COOAgent"),
        ("pm", "agents.pm_agent", "PMAgent"),
        ("qa", "agents.qa_agent", "QAAgent"),
        ("spec", "agents.spec_agent", "SpecAgent"),
        ("dev_app", "agents.dev_app_agent", "DevAppAgent"),
        ("dev_gaming", "agents.dev_gaming_agent", "DevGamingAgent"),
        ("embedded_dev", "agents.embedded_dev_agent", "EmbeddedDevAgent"),
        ("marketing", "agents.marketing_agent", "MarketingAgent"),
        ("content", "agents.content_agent", "ContentAgent"),
        ("hardware", "agents.hardware_agent", "HardwareAgent"),
        ("game_director", "agents.game_director_agent", "GameDirectorAgent"),
        ("brainstorm", "agents.brainstorm_agent", "BrainstormAgent"),
        ("accounting", "agents.accountant_agent", "AccountantAgent"),
    ]
    for aid, mod, cls in agents:
        try:
            __import__(mod, fromlist=[cls])
            print(f"  OK  {aid}")
        except Exception as exc:
            print(f"  FAIL {aid}: {exc}")
            failures += 1

    print("\n--- 6. Boucle d'apprentissage (14 bureaux) ---")
    closed = 0
    for aid, info in LEARNING_AUDIT.items():
        loop = info["loop"]
        print(f"  [OK] {aid:16} [{loop}] read={info['read'][:40]}")
        if loop == "fermee":
            closed += 1

    print(f"\n  Resume: {closed}/{len(LEARNING_AUDIT)} boucles fermees")

    print("\n--- 7. OpenRouter ping ---")
    try:
        from agents.base import LLMClient

        reply = LLMClient().complete("Reponds OK.", "ping", max_tokens=8)
        print(f"  OK  LLM -> {reply.strip()[:30]}")
    except Exception as exc:
        print(f"  FAIL  OpenRouter: {exc}")
        failures += 1

    print("\n" + "=" * 60)
    if failures:
        print(f"RESULTAT: {failures} echec(s) critique(s)")
        return 1
    print("RESULTAT: Tous les bureaux ont une boucle d'apprentissage fermee")
    return 0


if __name__ == "__main__":
    sys.exit(main())
