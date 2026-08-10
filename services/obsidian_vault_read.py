"""Obsidian vault — markdown read/parse helpers."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Iterator

from services.obsidian_vault_constants import SKIP_DIRS, VaultNote
from services.obsidian_vault_path import get_vault_path

logger = logging.getLogger(__name__)


def iter_markdown_files(
    vault: Path | None = None,
    *,
    subdir: str | None = None,
) -> Iterator[Path]:
    """Yield ``.md`` files under vault (optionally scoped to subdir)."""
    root = vault or get_vault_path()
    base = root / subdir if subdir else root
    if not base.is_dir():
        return

    for path in sorted(base.rglob("*.md")):
        if any(part in SKIP_DIRS for part in path.parts):
            continue
        if path.name.startswith("."):
            continue
        yield path


def _split_frontmatter(text: str) -> tuple[dict[str, Any], str]:
    """Parse optional YAML-like frontmatter between --- fences."""
    normalized = text.replace("\r\n", "\n")
    if not normalized.startswith("---"):
        return {}, normalized

    end = normalized.find("\n---", 3)
    if end < 0:
        return {}, normalized

    block = normalized[3:end].strip()
    body = normalized[end + 4 :].lstrip("\n")

    meta: dict[str, Any] = {}
    for line in block.splitlines():
        if ":" not in line:
            continue
        key, _, value = line.partition(":")
        key = key.strip().lower().replace(" ", "_")
        value = value.strip()
        if value.startswith("[") and value.endswith("]"):
            inner = value[1:-1].strip()
            meta[key] = [v.strip().strip("'\"") for v in inner.split(",") if v.strip()]
        elif value.lower() in {"true", "false"}:
            meta[key] = value.lower() == "true"
        else:
            meta[key] = value.strip("'\"")

    return meta, body


def _title_from_content(body: str, filename: str) -> str:
    for line in body.splitlines():
        stripped = line.strip()
        if stripped.startswith("#"):
            return stripped.lstrip("#").strip()
    return Path(filename).stem.replace("-", " ").title()


def read_note(path: Path, vault: Path | None = None) -> VaultNote:
    """Read a single note; ``path`` may be absolute or relative to vault."""
    root = vault or get_vault_path()
    file_path = path if path.is_absolute() else root / path
    raw = file_path.read_text(encoding="utf-8")
    meta, body = _split_frontmatter(raw)
    rel = str(file_path.relative_to(root)).replace("\\", "/")
    return VaultNote(
        rel_path=rel,
        title=_title_from_content(body, file_path.name),
        content=body.strip(),
        metadata=meta,
    )


def list_notes(
    *,
    subdir: str | None = None,
    vault: Path | None = None,
) -> list[VaultNote]:
    root = vault or get_vault_path()
    notes: list[VaultNote] = []
    for file_path in iter_markdown_files(root, subdir=subdir):
        try:
            notes.append(read_note(file_path, vault=root))
        except OSError as exc:
            logger.warning("Skip unreadable note %s: %s", file_path, exc)
    return notes


def find_notes_by_ref_prefix(prefix: str, vault: Path | None = None) -> list[VaultNote]:
    """Find notes whose ``ref`` metadata starts with prefix (case-insensitive)."""
    needle = prefix.strip().upper()
    return [n for n in list_notes(vault=vault) if (n.ref or "").upper().startswith(needle)]
