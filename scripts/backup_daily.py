#!/usr/bin/env python3
"""
backup_daily.py — Export critical ALNUA Hub data for disaster recovery.

Exports:
  - data/*.json (cost_log, event_log, agent_scores, coding_errors, etc.)
  - skills/ auto-generated content
  - .env.example (never .env with secrets)

Usage:
    python scripts/backup_daily.py
    python scripts/backup_daily.py --output backups/2026-07-09
"""

from __future__ import annotations

import argparse
import json
import shutil
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_OUTPUT = ROOT / "backups" / date.today().isoformat()

DATA_GLOBS = ("*.json",)
SKILL_DIRS = ("skills",)
EXTRA_FILES = (".env.example", "CLAUDE.md", "docs/API_ROUTES.md")


def export_json_snapshot(src_dir: Path, dest_dir: Path) -> int:
    count = 0
    if not src_dir.exists():
        return 0
    dest_dir.mkdir(parents=True, exist_ok=True)
    for pattern in DATA_GLOBS:
        for f in src_dir.glob(pattern):
            shutil.copy2(f, dest_dir / f.name)
            count += 1
    return count


def export_directory(src: Path, dest: Path) -> int:
    if not src.exists():
        return 0
    if dest.exists():
        shutil.rmtree(dest)
    shutil.copytree(src, dest, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
    return sum(1 for _ in dest.rglob("*") if _.is_file())


def write_manifest(output: Path, stats: dict) -> None:
    manifest = {
        "date": date.today().isoformat(),
        "hub_root": str(ROOT),
        "stats": stats,
    }
    (output / "manifest.json").write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )


def upload_to_s3(local_dir: Path) -> bool:
    """Upload backup folder to S3 if BACKUP_S3_BUCKET is configured."""
    try:
        from config.settings import get_settings
        settings = get_settings()
        bucket = settings.backup_s3_bucket.strip()
        if not bucket:
            return False
        import boto3

        s3 = boto3.client(
            "s3",
            region_name=settings.aws_region,
            aws_access_key_id=settings.aws_access_key_id or None,
            aws_secret_access_key=settings.aws_secret_access_key or None,
        )
        prefix = settings.backup_s3_prefix.rstrip("/") + "/" + local_dir.name
        uploaded = 0
        for f in local_dir.rglob("*"):
            if f.is_file():
                key = f"{prefix}/{f.relative_to(local_dir).as_posix()}"
                s3.upload_file(str(f), bucket, key)
                uploaded += 1
        print(f"☁️  S3 upload: s3://{bucket}/{prefix}/ ({uploaded} files)")
        return True
    except Exception as exc:
        print(f"⚠️  S3 upload skipped: {exc}")
        return False


def main() -> int:
    parser = argparse.ArgumentParser(description="ALNUA Hub daily backup")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()

    output: Path = args.output
    output.mkdir(parents=True, exist_ok=True)

    stats: dict[str, int | str] = {}

    data_dest = output / "data"
    stats["json_files"] = export_json_snapshot(ROOT / "data", data_dest)

    for skill_dir in SKILL_DIRS:
        src = ROOT / skill_dir
        if src.exists():
            stats[f"{skill_dir}_files"] = export_directory(src, output / skill_dir)

    for extra in EXTRA_FILES:
        src = ROOT / extra
        if src.exists():
            shutil.copy2(src, output / extra.replace("/", "_"))
            stats["extra_files"] = int(stats.get("extra_files", 0)) + 1

    write_manifest(output, stats)
    upload_to_s3(output)
    print(f"✅ Backup complete → {output}")
    print(f"   JSON files: {stats.get('json_files', 0)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
