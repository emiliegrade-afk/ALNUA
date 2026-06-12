import os
import sys

import requests
from dotenv import load_dotenv

load_dotenv()

results: dict[str, bool] = {}


def _status(ok: bool) -> str:
    return "[OK]" if ok else "[FAIL]"


# Test Supabase
print("\n[1/3] Test Supabase...")
try:
    from database.supabase_client import get_supabase

    supabase = get_supabase()
    res = supabase.table("projects").select("id").limit(1).execute()
    print(f"  {_status(True)} Supabase connecte — {len(res.data)} projet(s)")
    results["supabase"] = True
except Exception as e:
    print(f"  {_status(False)} {e}")
    results["supabase"] = False

# Test OpenRouter
print("\n[2/3] Test OpenRouter...")
try:
    key = os.getenv("OPENROUTER_API_KEY")
    r = requests.post(
        "https://openrouter.ai/api/v1/chat/completions",
        headers={"Authorization": f"Bearer {key}"},
        json={
            "model": "anthropic/claude-3-haiku",
            "messages": [{"role": "user", "content": "Reponds juste OK"}],
        },
        timeout=15,
    )
    reply = r.json()["choices"][0]["message"]["content"]
    print(f"  {_status(True)} OpenRouter OK — {reply}")
    results["openrouter"] = True
except Exception as e:
    print(f"  {_status(False)} {e}")
    results["openrouter"] = False

# Test COO Agent
print("\n[3/3] Test COO Agent...")
try:
    from agents.coo_agent import COOAgent

    result = COOAgent().handle_instruction("test")
    print(f"  {_status(True)} COO Agent OK — {str(result)[:80]}")
    results["coo_agent"] = True
except Exception as e:
    print(f"  {_status(False)} {e}")
    results["coo_agent"] = False

print("\n" + "=" * 35)
for key, ok in results.items():
    print(f"  {_status(ok)} {key}")

sys.exit(0 if all(results.values()) else 1)
