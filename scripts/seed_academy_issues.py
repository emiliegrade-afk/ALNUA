#!/usr/bin/env python3
"""
seed_academy_issues.py — Crée les issues GitHub pour l'Académie ALNUA.

Usage:
    python scripts/seed_academy_issues.py --level 1
    python scripts/seed_academy_issues.py --level 1 --dry-run
    python scripts/seed_academy_issues.py --all --mark-ready
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from dotenv import load_dotenv

load_dotenv(ROOT / ".env")


def main() -> int:
    parser = argparse.ArgumentParser(description="Seed ALNUA Academy GitHub issues")
    parser.add_argument("--level", type=int, choices=[1, 2, 3, 4], help="Niveau 1-4")
    parser.add_argument("--all", action="store_true", help="Tous les niveaux")
    parser.add_argument("--dry-run", action="store_true", help="Simuler sans créer")
    parser.add_argument(
        "--mark-ready",
        action="store_true",
        help="Label agent-ready sur la première issue ouverte du niveau",
    )
    args = parser.parse_args()

    if not args.level and not args.all:
        parser.error("Spécifier --level N ou --all")

    from services.academy_seed import seed_level

    levels = [1, 2, 3, 4] if args.all else [args.level]
    exit_code = 0

    for lv in levels:
        try:
            result = seed_level(
                lv,
                dry_run=args.dry_run,
                mark_first_ready=args.mark_ready and not args.all,
            )
            print(f"\n=== Niveau {lv} ===")
            print(f"  créées : {result['created_count']}")
            print(f"  ignorées (déjà là) : {result['skipped_count']}")
            for item in result.get("created", [])[:5]:
                print(f"  + {item.get('exercise_id')} {item.get('title', item.get('url', ''))}")
            if result.get("first_agent_ready"):
                print(f"  agent-ready : {result['first_agent_ready']}")
        except ValueError as exc:
            print(f"[ERREUR] Niveau {lv}: {exc}")
            exit_code = 1

    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
