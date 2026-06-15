"""Detailed CreatorFlow dispatch audit from agent_logs."""
from __future__ import annotations

import json
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from database.supabase_client import get_supabase


def main() -> int:
    db = get_supabase()
    logs = db.select("agent_logs", limit=500)

    cf_logs = [
        l
        for l in logs
        if "creatorflow" in json.dumps(l, ensure_ascii=False).lower()
        or (l.get("action") or "").startswith("rnd_dispatch")
    ]

    print(f"Total agent_logs: {len(logs)}")
    print(f"CreatorFlow / dispatch logs: {len(cf_logs)}\n")

    by_action: dict[str, list] = defaultdict(list)
    for l in cf_logs:
        by_action[l.get("action") or "?"].append(l)

    for action in sorted(by_action.keys()):
        rows = sorted(by_action[action], key=lambda x: x.get("created_at", ""))
        print(f"=== {action} ({len(rows)}) ===")
        for l in rows:
            created = (l.get("created_at") or "")[:19]
            agent = l.get("agent_name")
            status = l.get("status")
            inp = (l.get("input_summary") or "")[:100].replace("\n", " ")
            out = (l.get("output_summary") or "")[:100].replace("\n", " ")
            print(f"  [{created}] {agent} | {status}")
            if inp:
                print(f"    in:  {inp}")
            if out and out != inp:
                print(f"    out: {out}")
        print()

    # Roadmap with CreatorFlow in title
    roadmap = db.select("roadmap", limit=100)
    cf_roadmap = [r for r in roadmap if "creatorflow" in (r.get("title") or "").lower()]
    print(f"=== ROADMAP CreatorFlow ({len(cf_roadmap)}) ===")
    for r in sorted(cf_roadmap, key=lambda x: x.get("created_at", "")):
        print(
            f"  [{r.get('created_at', '')[:19]}] [{r.get('status')}] {r.get('title')} | project={r.get('project_id')}"
        )

    # Projects
    projects = db.select("projects", limit=50)
    cf_projects = [p for p in projects if "creatorflow" in json.dumps(p, ensure_ascii=False).lower()]
    print(f"\n=== PROJECTS CreatorFlow ({len(cf_projects)}) ===")
    for p in cf_projects:
        print(f"  {p.get('id')} | {p.get('name')} | {p.get('slug', p.get('title', ''))}")

    # Dossiers count
    dossiers = db.select("rnd_dossiers", limit=10)
    print(f"\n=== RND DOSSIERS in DB: {len(dossiers)} ===")

    return 0


if __name__ == "__main__":
    sys.exit(main())
