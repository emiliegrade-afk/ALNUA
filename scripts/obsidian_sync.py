#!/usr/bin/env python3
"""Sync Obsidian vault lore/GDD → Supabase for Hub agents."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from dotenv import load_dotenv

load_dotenv(ROOT / ".env")

from config.settings import settings
from database.supabase_client import get_supabase
from services.obsidian_sync import run_full_sync, sync_gdd_files, sync_lore_entries
from services.obsidian_vault import get_vault_path


def main() -> int:
    parser = argparse.ArgumentParser(description="Sync Obsidian vault to Supabase")
    parser.add_argument("--lore-only", action="store_true")
    parser.add_argument("--gdd-only", action="store_true")
    parser.add_argument("--dry-run", action="store_true", help="Report without writing")
    parser.add_argument("--vault", help="Override OBSIDIAN_VAULT_PATH")
    parser.add_argument(
        "--project-slug",
        default=settings.obsidian_gaming_project_slug or "wyrdheim",
    )
    args = parser.parse_args()

    vault = Path(args.vault) if args.vault else get_vault_path()
    if not vault.is_dir():
        print(f"Vault not found: {vault}", file=sys.stderr)
        print("Run: python scripts/bootstrap_obsidian_vault.py", file=sys.stderr)
        return 1

    db = get_supabase()

    if args.lore_only:
        result = sync_lore_entries(db, vault=vault, dry_run=args.dry_run)
    elif args.gdd_only:
        result = sync_gdd_files(
            db,
            vault=vault,
            project_slug=args.project_slug,
            dry_run=args.dry_run,
        )
    else:
        result = run_full_sync(
            db,
            vault=vault,
            project_slug=args.project_slug,
            dry_run=args.dry_run,
        )

    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
