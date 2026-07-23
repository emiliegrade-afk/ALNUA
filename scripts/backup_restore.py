#!/usr/bin/env python3
"""Restore ALNUA Hub backup from local folder or S3."""

from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def restore_local(backup_dir: Path, *, dry_run: bool = False) -> int:
    if not backup_dir.exists():
        print(f"❌ Backup not found: {backup_dir}")
        return 1

    manifest = backup_dir / "manifest.json"
    if not manifest.exists():
        print(f"⚠️  No manifest.json in {backup_dir}")

    data_src = backup_dir / "data"
    if data_src.exists():
        dest = ROOT / "data"
        if dry_run:
            print(f"[dry-run] Would restore {data_src} → {dest}")
        else:
            dest.mkdir(parents=True, exist_ok=True)
            for f in data_src.glob("*.json"):
                shutil.copy2(f, dest / f.name)
            print(f"✅ Restored data/ ({len(list(data_src.glob('*.json')))} files)")

    skills_src = backup_dir / "skills"
    if skills_src.exists() and not dry_run:
        print(f"ℹ️  Skills backup at {skills_src} — merge manually if needed")

    print("✅ Restore complete")
    return 0


def download_from_s3(prefix: str, dest: Path) -> bool:
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
        dest.mkdir(parents=True, exist_ok=True)
        paginator = s3.get_paginator("list_objects_v2")
        count = 0
        for page in paginator.paginate(Bucket=bucket, Prefix=prefix):
            for obj in page.get("Contents", []):
                key = obj["Key"]
                rel = key[len(prefix) :].lstrip("/")
                if not rel:
                    continue
                target = dest / rel
                target.parent.mkdir(parents=True, exist_ok=True)
                s3.download_file(bucket, key, str(target))
                count += 1
        print(f"☁️  Downloaded {count} files from s3://{bucket}/{prefix}")
        return count > 0
    except Exception as exc:
        print(f"❌ S3 download failed: {exc}")
        return False


def main() -> int:
    parser = argparse.ArgumentParser(description="ALNUA Hub backup restore")
    parser.add_argument("--backup", type=Path, help="Local backup directory")
    parser.add_argument("--s3-prefix", type=str, help="S3 prefix under BACKUP_S3_PREFIX")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    if args.s3_prefix:
        tmp = ROOT / "backups" / "_restore_tmp"
        if download_from_s3(args.s3_prefix, tmp):
            return restore_local(tmp, dry_run=args.dry_run)
        return 1

    if args.backup:
        return restore_local(args.backup, dry_run=args.dry_run)

    print("Usage: backup_restore.py --backup backups/2026-07-09")
    return 1


if __name__ == "__main__":
    sys.exit(main())
