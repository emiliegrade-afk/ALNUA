"""
obsidian_sync.py — Push vault lore/GDD markdown into Supabase for agent RAG.

v1: filesystem scan only (no Obsidian REST API). Idempotent upsert by vault path tag.
"""

from __future__ import annotations

import logging
import re
from pathlib import Path
from typing import Any

from services.gdd_manager import ingest_gdd
from services.obsidian_vault import (
    get_vault_path,
    iter_markdown_files,
    lore_note_to_entry,
    read_note,
)

logger = logging.getLogger(__name__)

REF_IN_TITLE = re.compile(r"^(LORE-[A-Z]+-\d+)", re.IGNORECASE)


def _resolve_gaming_project_id(db: Any, slug: str) -> str | None:
    """Find gaming branch project UUID by slug or name."""
    slug_l = slug.strip().lower()
    try:
        rows = (
            db.table("projects")
            .select("id, slug, name, branch")
            .eq("branch", "gaming")
            .execute()
            .data
            or []
        )
    except Exception as exc:
        logger.warning("projects lookup failed: %s", exc)
        return None

    for row in rows:
        row_slug = (row.get("slug") or "").lower()
        row_name = (row.get("name") or "").lower()
        if row_slug == slug_l or row_name == slug_l or slug_l in row_name:
            return row["id"]
    return rows[0]["id"] if rows else None


def _find_lore_by_vault_path(db: Any, vault_path: str) -> dict[str, Any] | None:
    """Match existing lore row tagged with vault path."""
    try:
        result = (
            db.table("lore_entries")
            .select("id, title, tags")
            .contains("tags", [f"vault:{vault_path}"])
            .limit(1)
            .execute()
        )
        rows = result.data or []
        return rows[0] if rows else None
    except Exception:
        return None


def sync_lore_entries(
    db: Any,
    *,
    vault: Path | None = None,
    subdir: str = "wyrdheim/lore",
    dry_run: bool = False,
) -> dict[str, Any]:
    """
    Scan ``wyrdheim/lore/*.md`` (and naia if present) → upsert ``lore_entries``.
    """
    root = vault or get_vault_path()
    lore_root = root / subdir
    if not lore_root.is_dir():
        return {"synced": 0, "skipped": 0, "errors": [], "message": f"Missing {lore_root}"}

    synced = 0
    skipped = 0
    errors: list[str] = []

    # Also sync naia-tagged lore from the same folder (project: naia_world in frontmatter)
    for file_path in iter_markdown_files(root, subdir=subdir):
        if file_path.name.endswith("-template.md") or "template" in file_path.parts:
            skipped += 1
            continue
        try:
            note = read_note(file_path, vault=root)
            payload = lore_note_to_entry(note)
            if not payload:
                skipped += 1
                continue

            vault_tag = f"vault:{note.rel_path}"
            tags = list(payload.pop("tags", []))
            if vault_tag not in tags:
                tags.append(vault_tag)
            ref_tag = payload.pop("_ref", None)
            payload.pop("_vault_path", note.rel_path)
            if ref_tag:
                tags.append(f"ref:{ref_tag}")

            row = {
                "title": payload["title"],
                "category": payload["category"],
                "project": payload["project"],
                "content": payload["content"],
                "tags": tags,
            }
            if note.ref:
                try:
                    from services.nomenclature import validate_ref

                    if validate_ref(note.ref):
                        row["ref_id"] = note.ref.upper()
                    else:
                        errors.append(f"{file_path.name}: invalid ref {note.ref}")
                except Exception:
                    row["ref_id"] = note.ref.upper()

            if dry_run:
                synced += 1
                continue

            existing = _find_lore_by_vault_path(db, note.rel_path)
            if existing:
                db.table("lore_entries").update(row).eq("id", existing["id"]).execute()
            else:
                db.table("lore_entries").insert(row).execute()
            synced += 1
        except Exception as exc:
            errors.append(f"{file_path.name}: {exc}")
            logger.exception("lore sync failed for %s", file_path)

    return {"synced": synced, "skipped": skipped, "errors": errors}


def sync_gdd_files(
    db: Any,
    *,
    vault: Path | None = None,
    project_slug: str = "wyrdheim",
    subdir: str = "wyrdheim/gdd",
    dry_run: bool = False,
) -> dict[str, Any]:
    """Ingest each GDD markdown under ``wyrdheim/gdd/`` into ``gdd_chunks``."""
    root = vault or get_vault_path()
    gdd_dir = root / subdir
    if not gdd_dir.is_dir():
        return {"ingested": 0, "errors": [], "message": f"Missing {gdd_dir}"}

    project_id = _resolve_gaming_project_id(db, project_slug)
    if not project_id:
        return {
            "ingested": 0,
            "errors": [],
            "message": f"No gaming project found for slug={project_slug}",
        }

    ingested = 0
    errors: list[str] = []

    for file_path in iter_markdown_files(root, subdir=subdir):
        if "template" in file_path.name.lower():
            continue
        try:
            note = read_note(file_path, vault=root)
            ref = (note.ref or "").upper()
            if ref and not ref.startswith("GDD-"):
                continue
            if not note.content.strip():
                continue

            if dry_run:
                ingested += 1
                continue

            try:
                db.table("gdd_chunks").delete().eq("source_filename", note.rel_path).execute()
            except Exception:
                pass

            ingest_gdd(
                db,
                project_id=project_id,
                markdown=note.content,
                document_title=note.title,
                source_filename=note.rel_path,
                replace_existing=False,
            )
            ingested += 1
        except Exception as exc:
            errors.append(f"{file_path.name}: {exc}")
            logger.exception("gdd sync failed for %s", file_path)

    return {
        "ingested": ingested,
        "errors": errors,
        "project_id": project_id,
        "project_slug": project_slug,
    }


def run_full_sync(
    db: Any,
    *,
    vault: Path | None = None,
    project_slug: str = "wyrdheim",
    dry_run: bool = False,
) -> dict[str, Any]:
    """Lore + GDD sync in one call."""
    lore = sync_lore_entries(db, vault=vault, dry_run=dry_run)
    gdd = sync_gdd_files(
        db, vault=vault, project_slug=project_slug, dry_run=dry_run
    )
    return {"lore": lore, "gdd": gdd, "dry_run": dry_run}
