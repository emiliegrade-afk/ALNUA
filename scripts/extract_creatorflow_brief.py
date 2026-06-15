import ast
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from database.supabase_client import get_supabase

db = get_supabase()
logs = db.select("agent_logs", limit=500)

for l in logs:
    if l.get("action") == "rnd_dispatch_brief" and "CreatorFlow" in (l.get("input_summary") or ""):
        print("=== BRIEF COO CreatorFlow ===")
        print("time:", l.get("created_at"))
        print("status:", l.get("status"))
        print("input:", l.get("input_summary"))
        out = l.get("output_summary") or ""
        try:
            payload = ast.literal_eval(out[:4000])
            for it in payload.get("roadmap_items") or []:
                print(" roadmap:", it)
            print("matrix:")
            for row in payload.get("matrix") or []:
                print(
                    " ",
                    row.get("pole"),
                    "->",
                    row.get("agent_id"),
                    "|",
                    row.get("deliverables"),
                )
        except Exception as e:
            print("parse err", e)
            print(out[:800])
        break

for l in logs:
    if l.get("action") == "plan_execution" and "CreatorFlow" in (l.get("input_summary") or ""):
        print("\n=== PLAN EXECUTION ===")
        print("time:", l.get("created_at"))
        print("out:", (l.get("output_summary") or "")[:1500])
