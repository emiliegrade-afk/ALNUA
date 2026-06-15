"""Check CreatorFlow dossier dispatch status and agent mission transmission."""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from database.supabase_client import get_supabase


def main() -> int:
    db = get_supabase()

    dossiers = db.select("rnd_dossiers", filters={"slug": "creatorflow"}, limit=5)
    if not dossiers:
        all_d = db.select("rnd_dossiers", limit=100)
        dossiers = [
            d
            for d in all_d
            if "creatorflow" in (d.get("slug", "") + d.get("title", "")).lower()
        ]

    print("=== DOSSIERS CREATORFLOW ===")
    if not dossiers:
        print("Aucun dossier CreatorFlow trouvé en base.")
        return 1

    for d in dossiers:
        print(
            json.dumps(
                {
                    k: d.get(k)
                    for k in [
                        "id",
                        "slug",
                        "title",
                        "status",
                        "ceo_status",
                        "dispatch_status",
                        "branch",
                        "domain",
                    ]
                },
                indent=2,
                ensure_ascii=False,
            )
        )

    dossier = dossiers[0]
    dossier_id = dossier["id"]
    dj = dossier.get("dispatch_json")
    if isinstance(dj, str):
        dj = json.loads(dj)

    project_id = None
    if isinstance(dj, dict):
        project_id = dj.get("project_id")
        print("\n=== DISPATCH JSON ===")
        print("project_id:", project_id)
        print("dispatched_at:", dj.get("dispatched_at"))
        print("execution_status:", dj.get("execution_status"))
        print("execution_run_id:", dj.get("execution_run_id"))
        print("roadmap_items:", len(dj.get("roadmap_items") or []))
        for item in dj.get("roadmap_items") or []:
            print(
                "  -",
                item.get("pole"),
                "| agent:",
                item.get("agent_id"),
                "|",
                (item.get("title") or "")[:60],
            )
        print("matrix:", len(dj.get("matrix") or []))
        for row in dj.get("matrix") or []:
            print(
                "  -",
                row.get("pole"),
                "| agent:",
                row.get("agent_id"),
                "| priority:",
                row.get("priority"),
            )

    print("\n=== AGENT LOGS (dispatch) ===")
    logs = db.select("agent_logs", limit=200)
    relevant: list[dict] = []
    for l in logs:
        blob = json.dumps(l, ensure_ascii=False).lower()
        if "creatorflow" in blob or str(dossier_id) in blob:
            relevant.append(l)
        elif "rnd_dispatch" in (l.get("action") or ""):
            if project_id and l.get("project_id") == project_id:
                relevant.append(l)

    seen: set[str] = set()
    for l in sorted(relevant, key=lambda x: x.get("created_at", ""), reverse=True):
        lid = str(l.get("id", ""))
        if lid in seen:
            continue
        seen.add(lid)
        created = (l.get("created_at") or "")[:19]
        print(
            f"  [{created}] {l.get('agent_name')} / {l.get('action')} / status={l.get('status')}"
        )
        print(f"    in: {(l.get('input_summary') or '')[:150]}")
        print(f"    out: {(l.get('output_summary') or '')[:150]}")

    if not relevant:
        print("  (aucun log dispatch trouvé)")

    if project_id:
        print("\n=== ROADMAP ITEMS ===")
        items = db.select("roadmap", filters={"project_id": project_id}, limit=30)
        for it in items:
            print(
                f"  - [{it.get('status')}] {(it.get('title') or '')[:70]} | priority={it.get('priority')}"
            )
        if not items:
            print("  (aucune entrée roadmap)")

    print("\n=== RND EVENTS ===")
    events = db.select("rnd_dossier_events", filters={"dossier_id": dossier_id}, limit=20)
    for ev in sorted(events, key=lambda x: x.get("created_at", "")):
        print(
            f"  [{ev.get('created_at', '')[:19]}] {ev.get('event_type')} by {ev.get('actor')}"
        )

    return 0


if __name__ == "__main__":
    sys.exit(main())
