#!/usr/bin/env python3
"""CLI — allocate next ALNUA reference ID (Obsidian / agents)."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from dotenv import load_dotenv

load_dotenv(ROOT / ".env")

from services.nomenclature import (
    create_obsidian_stub,
    next_ref,
    parse_ref,
    peek_next_ref,
    reconcile_vault,
    suggest_obsidian_path,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="ALNUA nomenclature — next ref ID")
    parser.add_argument(
        "kind",
        choices=["APP", "GDD", "LORE", "ASSET", "BUG", "COLLAB", "RND"],
        help="Reference family",
    )
    parser.add_argument("--slug", help="Slug (app name, biome, partner, etc.)")
    parser.add_argument("--scope", choices=["WYR", "NWA"], help="Wyrdheim or Naïa World")
    parser.add_argument(
        "--subtype",
        choices=["ENV", "CHAR", "VFX", "MAT", "SFX"],
        help="Asset subtype (ASSET only)",
    )
    parser.add_argument("--feature", action="store_true", help="APP feature ref (F00n)")
    parser.add_argument("--peek", action="store_true", help="Preview without incrementing")
    parser.add_argument("--create", action="store_true", help="Create Obsidian note stub")
    parser.add_argument("--title", help="Note title when --create")
    parser.add_argument("--validate", metavar="REF", help="Validate a ref string")
    parser.add_argument("--reconcile", action="store_true", help="Sync counters from vault")
    args = parser.parse_args()

    if args.validate:
        p = parse_ref(args.validate)
        print(json.dumps({"valid": p is not None, "parsed": p.to_dict() if p else None}, indent=2))
        return 0 if p else 1

    if args.reconcile:
        print(json.dumps(reconcile_vault(), indent=2, ensure_ascii=False))
        return 0

    kind = args.kind.upper()
    if args.peek:
        ref = peek_next_ref(
            kind,  # type: ignore[arg-type]
            slug=args.slug,
            scope=args.scope,
            subtype=args.subtype,
            feature=args.feature,
        )
    else:
        ref = next_ref(
            kind,  # type: ignore[arg-type]
            slug=args.slug,
            scope=args.scope,
            subtype=args.subtype,
            feature=args.feature,
        )

    out: dict = {"ref": ref, "path": suggest_obsidian_path(ref)}
    if args.create:
        out["note"] = create_obsidian_stub(ref, title=args.title)
    print(json.dumps(out, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
