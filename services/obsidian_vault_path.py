"""Obsidian vault — path resolution and layout bootstrap."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from config.settings import settings

from services.obsidian_vault_constants import CANONICAL_VAULT, VAULT_LAYOUT_DIRS

logger = logging.getLogger(__name__)


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
    root = CANONICAL_VAULT.parent.parent

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

    c_fallback = root.parent / "ObsidianVault"
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
