from database.supabase_client import get_supabase

db = get_supabase()
rows = (
    db.table("agent_error_journal")
    .select("*")
    .order("created_at", desc=True)
    .limit(5)
    .execute()
)
for row in rows.data or []:
    print("---")
    for k in ("created_at", "agent_name", "error_type", "status", "message", "context"):
        if row.get(k):
            val = str(row[k])
            print(f"{k}: {val[:300]}")
