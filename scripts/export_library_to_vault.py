#!/usr/bin/env python3
"""
One-shot / incremental export: bureau_library.json → Obsidian vault + topic catalog.

Usage:
    python scripts/export_library_to_vault.py
    python scripts/export_library_to_vault.py --index-chroma
    python scripts/export_library_to_vault.py --limit 50
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from dotenv import load_dotenv

load_dotenv(ROOT / ".env")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Export ALNUA bureau library to Obsidian vault + topic catalog"
    )
    parser.add_argument(
        "--index-chroma",
        action="store_true",
        help="Also index library/*.md into Chroma collection alnua_library",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Optional cap on entries (smoke tests)",
    )
    parser.add_argument(
        "--ensure-layout-only",
        action="store_true",
        help="Only create vault folders, do not export entries",
    )
    args = parser.parse_args()

    from services.obsidian_vault import ensure_vault_layout, get_vault_path

    vault = get_vault_path()
    layout = ensure_vault_layout(vault)
    if args.ensure_layout_only:
        print(json.dumps({"ok": True, "layout": layout}, indent=2, ensure_ascii=False))
        return 0

    from services.library_vault_export import export_library_to_vault

    result = export_library_to_vault(
        vault=vault,
        limit=args.limit,
        index_chroma=args.index_chroma,
    )
    print(json.dumps(result, indent=2, ensure_ascii=False))
    print(f"\nVault: {result.get('vault')}")
    print(f"Notes written: {result.get('written')} · topics: {result.get('topic_count')}")
    print("Open Obsidian on this vault — see library/_index/TOPICS.md")
    return 0 if result.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
