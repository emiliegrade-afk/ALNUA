"""
obsidian_vault.py — Read and parse the local Obsidian vault (filesystem).

Vault canonical copy lives in ``vault/obsidian/``; runtime path from OBSIDIAN_VAULT_PATH.
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterator

from config.settings import settings

logger = logging.getLogger(__name__)

ROOT = Path(__file__).resolve().parent.parent
CANONICAL_VAULT = ROOT / "vault" / "obsidian"

SKIP_DIRS = {".obsidian", ".trash", ".git", "__pycache__"}
LORE_CATEGORIES = frozenset(
    {"factions", "personnages", "lieux", "histoire", "magie", "economie", "quetes"}
)
LORE_PROJECTS = frozenset({"wyrdheim", "naia_world", "shared"})

# Memory / library layout — one central vault, namespaced folders
VAULT_LAYOUT_DIRS: tuple[str, ...] = (
    "wyrdheim/lore",
    "wyrdheim/gdd",
    "wyrdheim/biomes",
    "wyrdheim/creatures",
    "apps",
    "rnd",
    "collabs",
    "daily",
    "library",
    "library/_index",
    "library/_digests",
    "library/hub",
    "library/secretary",
    "library/app",
    "library/gaming",
    "library/robo",
    "library/marketing",
    "library/rd",
    "library/finances",
    "library/analytics",
    "library/academy",
    "memory",
    "memory/agents",
)


@dataclass
class VaultNote:
    """One markdown note relative to vault root."""

    rel_path: str
    title: str
    content: str
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def ref(self) -> str | None:
        ref = self.metadata.get("ref")
        if ref:
            return str(ref).strip()
        match = re.search(
            r"^(?:ref:\s*)?((?:APP|GDD|LORE|BUG|COLLAB|RND|ASSET)-[\w-]+)",
            self.content,
            re.MULTILINE | re.IGNORECASE,
        )
        return match.group(1) if match else None


def _drive_root_exists(path: Path) -> bool:
    """True if the drive/volume for ``path`` is reachable (Windows-friendly)."""
    try:
        return path.drive == "" or Path(path.anchor).exists()
    except OSError:
        return False


def resolve_bootstrap_target(
    explicit: Path | None = None,
    *,
    allow_c_fallback: bool = False,
) -> tuple[Path, str]:
    """
    Pick where to create the user vault.

    Returns ``(path, reason)``. Preferred location is always ``D:\\ObsidianVault``
    (Kingston SSD). Does **not** silently write to ``C:\\`` unless
    ``allow_c_fallback=True``.
    """
    preferred = Path(r"D:\ObsidianVault")

    if explicit is not None:
        if not _drive_root_exists(explicit):
            raise OSError(
                f"Drive not available for path: {explicit}. "
                "Mount the SSD or choose another --target."
            )
        return explicit, "cli --target"

    configured = (settings.obsidian_vault_path or "").strip()
    if configured:
        path = Path(configured).expanduser()
        if _drive_root_exists(path):
            return path, "OBSIDIAN_VAULT_PATH"
        raise OSError(
            f"OBSIDIAN_VAULT_PATH is set to {path} but that drive/path is not reachable. "
            f"Mount the disk or run: python scripts/bootstrap_obsidian_vault.py "
            f"--target {preferred}"
        )

    if _drive_root_exists(preferred):
        return preferred, "default D:\\ObsidianVault"

    c_fallback = ROOT.parent / "ObsidianVault"
    if allow_c_fallback and _drive_root_exists(c_fallback):
        return c_fallback, "emergency C:\\Dev\\ObsidianVault (D: missing)"

    raise OSError(
        "D:\\ is not available - your vault should live on the Kingston SSD at "
        f"{preferred}. Mount D: in Disk Management, then run:\n"
        f"  python scripts/bootstrap_obsidian_vault.py --target {preferred}\n"
        "Emergency only (vault on C:): add --allow-c-fallback"
    )


def get_vault_path() -> Path:
    """Resolved vault directory — falls back to canonical repo copy."""
    configured = (settings.obsidian_vault_path or "").strip()
    if configured:
        path = Path(configured).expanduser()
        if path.is_dir():
            return path
        logger.warning("OBSIDIAN_VAULT_PATH not found: %s — using canonical copy", path)
    return CANONICAL_VAULT


def get_canonical_vault_path() -> Path:
    return CANONICAL_VAULT


def ensure_vault_layout(vault: Path | None = None) -> dict[str, Any]:
    """
    Create the standard ALNUA vault folder scaffold (library, memory, projects).

    Safe to call repeatedly — only creates missing directories and placeholder
    ``.gitkeep`` / index stubs when absent.
    """
    root = vault or get_vault_path()
    root.mkdir(parents=True, exist_ok=True)

    created: list[str] = []
    existing: list[str] = []

    for folder in VAULT_LAYOUT_DIRS:
        path = root / folder
        if path.is_dir():
            existing.append(folder)
        else:
            path.mkdir(parents=True, exist_ok=True)
            created.append(folder)

    # Lightweight placeholders so empty dirs survive sync tools
    for folder in (
        "apps",
        "rnd",
        "collabs",
        "daily",
        "library/_digests",
        "memory/agents",
    ):
        keep = root / folder / ".gitkeep"
        if not keep.exists():
            keep.write_text("", encoding="utf-8")
            created.append(str(keep.relative_to(root)).replace("\\", "/"))

    index_readme = root / "library" / "_index" / "README.md"
    if not index_readme.exists():
        index_readme.write_text(
            "# Bibliothèque ALNUA\n\n"
            "Notes exportées depuis le Hub (`bureau_library.json`).\n\n"
            "- `TOPICS.md` — catalogue de sujets scannable par les agents\n"
            "- `../{bureau}/` — fiches par bureau\n"
            "- `../_digests/` — synthèses de sujets (learn on demand)\n",
            encoding="utf-8",
        )
        created.append("library/_index/README.md")

    memory_readme = root / "memory" / "README.md"
    if not memory_readme.exists():
        memory_readme.write_text(
            "# Mémoire agents\n\n"
            "Digests et leçons exportées par agent (`memory/agents/{agent_id}/`).\n"
            "La vérité durable reste ici + le catalogue Hub ; Mem0 ne garde que des leçons distillées.\n",
            encoding="utf-8",
        )
        created.append("memory/README.md")

    return {
        "vault": str(root),
        "created": created,
        "existing": existing,
        "created_count": len(created),
        "existing_count": len(existing),
    }


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


def lore_note_to_entry(note: VaultNote) -> dict[str, Any] | None:
    """
    Map a vault lore note to a ``lore_entries`` row payload.
    Returns None if the note is not a lore document.
    """
    ref = (note.ref or "").upper()
    if not ref.startswith("LORE-"):
        return None

    project = str(note.metadata.get("project", "wyrdheim")).strip().lower()
    if project not in LORE_PROJECTS:
        if "NWA" in ref:
            project = "naia_world"
        else:
            project = "wyrdheim"

    category = str(note.metadata.get("category", "histoire")).strip().lower()
    if category not in LORE_CATEGORIES:
        category = "histoire"

    tags = note.metadata.get("tags", [])
    if isinstance(tags, str):
        tags = [t.strip() for t in tags.split(",") if t.strip()]

    content = note.content.strip()
    if not content:
        return None

    return {
        "title": note.title[:500],
        "category": category,
        "project": project,
        "content": content[:50_000],
        "tags": tags,
        "_vault_path": note.rel_path,
        "_ref": ref,
    }


def bootstrap_vault(target: Path | None = None, *, force: bool = False) -> dict[str, Any]:
    """
    Copy canonical ``vault/obsidian`` tree into the user vault.
    Skips existing files unless ``force=True``.
    """
    dest = target or get_vault_path()
    dest.mkdir(parents=True, exist_ok=True)

    copied: list[str] = []
    skipped: list[str] = []

    for src in CANONICAL_VAULT.rglob("*"):
        if src.is_dir():
            continue
        rel = src.relative_to(CANONICAL_VAULT)
        out = dest / rel
        out.parent.mkdir(parents=True, exist_ok=True)
        if out.exists() and not force:
            skipped.append(str(rel).replace("\\", "/"))
            continue
        out.write_bytes(src.read_bytes())
        copied.append(str(rel).replace("\\", "/"))

    layout = ensure_vault_layout(dest)

    return {
        "target": str(dest),
        "copied": copied,
        "skipped": skipped,
        "copied_count": len(copied),
        "skipped_count": len(skipped),
        "layout": layout,
    }
