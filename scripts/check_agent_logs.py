"""Print recent agent logs and errors from Supabase."""

from database.supabase_client import get_supabase

db = get_supabase()

logs = (
    db.table("agent_logs")
    .select("agent_name,action,status,created_at")
    .order("created_at", desc=True)
    .limit(15)
    .execute()
)
print("=== Recent agent_logs ===")
for row in logs.data or []:
    ts = str(row.get("created_at", ""))[:19]
    print(f"  {ts} | {row.get('agent_name')} | {row.get('status')} | {row.get('action')}")

try:
    errs = (
        db.table("agent_error_journal")
        .select("agent_name,error_type,status,created_at")
        .order("created_at", desc=True)
        .limit(10)
        .execute()
    )
    print("\n=== agent_error_journal ===")
    for row in errs.data or []:
        ts = str(row.get("created_at", ""))[:19]
        print(f"  {ts} | {row.get('agent_name')} | {row.get('status')} | {row.get('error_type')}")
except Exception as exc:
    print(f"\nagent_error_journal: {exc}")
