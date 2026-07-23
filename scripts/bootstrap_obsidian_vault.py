#!/usr/bin/env python3
"""Bootstrap Obsidian vault from canonical Hub copy (vault/obsidian/)."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from dotenv import load_dotenv

load_dotenv(ROOT / ".env")

from services.obsidian_vault import bootstrap_vault, resolve_bootstrap_target


def main() -> int:
    parser = argparse.ArgumentParser(description="Bootstrap ALNUA Obsidian vault")
    parser.add_argument(
        "--target",
        help="Vault path (default: OBSIDIAN_VAULT_PATH or D:\\ObsidianVault)",
    )
    parser.add_argument(
        "--allow-c-fallback",
        action="store_true",
        help="If D: is missing, allow C:\\Dev\\ObsidianVault (not recommended)",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Overwrite existing files",
    )
    args = parser.parse_args()

    try:
        target, reason = resolve_bootstrap_target(
            Path(args.target) if args.target else None,
            allow_c_fallback=args.allow_c_fallback,
        )
        result = bootstrap_vault(target, force=args.force)
    except OSError as exc:
        print(f"Cannot create vault: {exc}", file=sys.stderr)
        return 1

    if reason.startswith("emergency"):
        print("\n*** WARNING: D: unavailable — vault created on C: instead. ***", file=sys.stderr)
        print("*** When Kingston is back, bootstrap to D:\\ObsidianVault and update .env ***\n", file=sys.stderr)

    print(json.dumps({**result, "reason": reason}, indent=2, ensure_ascii=False))
    print(f"\nVault ready at: {result['target']}")
    print("Open Obsidian -> Open vault -> point to this folder.")
    print("Exclude this path from OneDrive sync.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
