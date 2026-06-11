import os, sys, requests
from dotenv import load_dotenv
load_dotenv()

results = {}

# Test Supabase
print("\n[1/3] Test Supabase...")
try:
    from database.supabase_client import get_supabase
    supabase = get_supabase()
    res = supabase.table("projects").select("id").limit(1).execute()
    print(f"  ✅ Supabase connecté — {len(res.data)} projet(s)")
    results["supabase"] = True
except Exception as e:
    print(f"  ❌ {e}")
    results["supabase"] = False

# Test OpenRouter
print("\n[2/3] Test OpenRouter...")
try:
    key = os.getenv("OPENROUTER_API_KEY")
    r = requests.post("https://openrouter.ai/api/v1/chat/completions",
        headers={"Authorization": f"Bearer {key}"},
        json={"model": "anthropic/claude-3-haiku",
              "messages": [{"role": "user", "content": "Réponds juste OK"}]},
        timeout=15)
    reply = r.json()["choices"][0]["message"]["content"]
    print(f"  ✅ OpenRouter OK — {reply}")
    results["openrouter"] = True
except Exception as e:
    print(f"  ❌ {e}")
    results["openrouter"] = False

# Test COO Agent
print("\n[3/3] Test COO Agent...")
try:
    from agents.coo_agent import COOAgent
    result = COOAgent().run("Dis juste: Système opérationnel")
    print(f"  ✅ COO Agent OK — {str(result)[:80]}")
    results["coo_agent"] = True
except Exception as e:
    print(f"  ❌ {e}")
    results["coo_agent"] = False

print("\n" + "="*35)
for k, v in results.items():
    print(f"  {'✅' if v else '❌'} {k}")