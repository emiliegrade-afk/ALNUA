#!/usr/bin/env python3
"""
restore_backup.py — Restore ALNUA Hub data from a local backup folder.

Usage:
    python scripts/restore_backup.py backups/2026-07-09
    python scripts/restore_backup.py backups/2026-07-09 --dry-run
"""

from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def restore_backup(backup_dir: Path, *, dry_run: bool = False) -> dict[str, int]:
    stats = {"json_files": 0, "skill_files": 0}
    manifest = backup_dir / "manifest.json"
    if manifest.exists():
        print(f"📋 Manifest: {json.dumps(json.loads(manifest.read_text()), indent=2)[:500]}")

    data_src = backup_dir / "data"
    if data_src.exists():
        data_dest = ROOT / "data"
        data_dest.mkdir(parents=True, exist_ok=True)
        for f in data_src.glob("*.json"):
            dest = data_dest / f.name
            if dry_run:
                print(f"  [dry-run] would restore {f.name}")
            else:
                shutil.copy2(f, dest)
            stats["json_files"] += 1

    skills_src = backup_dir / "skills"
    if skills_src.exists():
        skills_dest = ROOT / "skills"
        if not dry_run:
            if skills_dest.exists():
                shutil.rmtree(skills_dest)
            shutil.copytree(skills_src, skills_dest)
        stats["skill_files"] = sum(1 for _ in skills_src.rglob("*") if _.is_file())
        print(f"  skills/ → {stats['skill_files']} files")

    return stats


def main() -> int:
    parser = argparse.ArgumentParser(description="Restore ALNUA Hub backup")
    parser.add_argument("backup_dir", type=Path, help="Path to backup folder")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    if not args.backup_dir.exists():
        print(f"❌ Backup not found: {args.backup_dir}")
        return 1

    print(f"{'[DRY RUN] ' if args.dry_run else ''}Restoring from {args.backup_dir}")
    stats = restore_backup(args.backup_dir, dry_run=args.dry_run)
    print(f"✅ Restore {'preview' if args.dry_run else 'complete'}")
    print(f"   JSON files: {stats['json_files']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
