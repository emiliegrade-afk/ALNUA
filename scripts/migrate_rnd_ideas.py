"""Migrate data/rnd_ideas.json → Supabase rnd_ideas table."""
from __future__ import annotations

import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")

from services.rnd_repository import get_rnd_repository  # noqa: E402


def main() -> int:
    repo = get_rnd_repository()
    if not repo._use_db:
        print("ERROR: Supabase rnd_ideas table unavailable.")
        print("Run migration: supabase/migrations/20260613120000_rnd_dossiers.sql")
        return 1

    count = repo.sync_all_json_to_db()
    ideas = repo.get_top_ideas(limit=100)
    print(f"Synced {count} ideas to Supabase.")
    print(f"Total ideas visible via repository: {len(ideas)}")
    for idea in ideas[:10]:
        print(
            f"  - {idea.title[:50]} | {idea.verdict} | "
            f"score={idea.score} | dossier={idea.dossier_id or '-'}"
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())
