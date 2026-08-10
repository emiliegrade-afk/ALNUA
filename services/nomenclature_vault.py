"""Obsidian vault integration for ALNUA reference IDs."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from services.nomenclature_constants import SCOPE_NWA
from services.nomenclature_ops import reconcile_refs
from services.nomenclature_parse import parse_ref


def reconcile_vault(vault: Path | None = None) -> dict[str, Any]:
    """Scan Obsidian vault notes and sync counters."""
    from services.obsidian_vault import get_vault_path, list_notes

    root = vault or get_vault_path()
    refs: list[str] = []
    for note in list_notes(vault=root):
        if note.ref:
            refs.append(note.ref)
    for path in root.rglob("*.md"):
        name = path.stem.upper()
        if parse_ref(name):
            refs.append(name)
    return reconcile_refs(list(dict.fromkeys(refs)))


def suggest_obsidian_path(ref: str) -> str | None:
    """Suggest vault-relative path for a new note."""
    p = parse_ref(ref)
    if not p:
        return None
    if p.kind == "LORE":
        return f"wyrdheim/lore/{ref}.md"
    if p.kind == "GDD":
        return f"wyrdheim/gdd/{ref}.md"
    if p.kind == "APP":
        return f"apps/{ref}.md"
    if p.kind == "BUG":
        return f"daily/{ref}.md"
    if p.kind == "COLLAB":
        return f"collabs/{ref}.md"
    if p.kind == "RND":
        return f"rnd/{ref}.md"
    if p.kind == "ASSET":
        return f"wyrdheim/gdd/{ref}.md"
    return None


def create_obsidian_stub(
    ref: str,
    *,
    vault: Path | None = None,
    title: str | None = None,
    overwrite: bool = False,
) -> dict[str, Any]:
    """
    Create a markdown stub in the vault from the matching template.
    """
    from services.obsidian_vault import get_canonical_vault_path, get_vault_path

    p = parse_ref(ref)
    if not p:
        raise ValueError(f"Invalid ref: {ref}")

    root = vault or get_vault_path()
    rel = suggest_obsidian_path(ref)
    if not rel:
        raise ValueError(f"No path mapping for {ref}")

    dest = root / rel
    if dest.exists() and not overwrite:
        return {"created": False, "path": str(dest), "reason": "exists"}

    template_name = {
        "APP": "APP-template.md",
        "GDD": "GDD-WYR-template.md",
        "LORE": "LORE-WYR-template.md" if p.scope != SCOPE_NWA else "LORE-NWA-template.md",
        "BUG": "BUG-template.md",
        "COLLAB": "COLLAB-template.md",
    }.get(p.kind)

    body = f"---\nref: {ref}\nstatut: draft\n---\n\n# {title or ref}\n\n"
    if template_name:
        tpl = get_canonical_vault_path() / "_templates" / template_name
        if tpl.is_file():
            body = tpl.read_text(encoding="utf-8")
            body = body.replace("{SLUG}", p.slug or "doc")
            body = re.sub(r"ref:\s*\S+", f"ref: {ref}", body, count=1)

    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(body, encoding="utf-8")
    return {"created": True, "path": str(dest), "rel_path": rel.replace("\\", "/")}
