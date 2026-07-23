"""
nomenclature.py — ALNUA reference IDs (APP-, LORE-WYR-, GDD-, BUG-, etc.).

Counters persist in ``data/nomenclature_counters.json``. Vault scan reconciles
sequence numbers so Obsidian and Hub stay aligned.
"""

from __future__ import annotations

import json
import logging
import re
import threading
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any, Literal

logger = logging.getLogger(__name__)

ROOT = Path(__file__).resolve().parent.parent
COUNTERS_FILE = ROOT / "data" / "nomenclature_counters.json"

RefKind = Literal[
    "APP",
    "GDD",
    "LORE",
    "ASSET",
    "BUG",
    "COLLAB",
    "RND",
]

SCOPE_WYR = "WYR"
SCOPE_NWA = "NWA"

_ASSET_SUBTYPES = frozenset({"ENV", "CHAR", "VFX", "MAT", "SFX", "APP"})

# APP-naia-001 | APP-naia-F003 | GDD-WYR-biome-001 | LORE-WYR-001 | LORE-NWA-012
# ASSET-WYR-ENV-001 | ASSET-APP-naia-001 | BUG-20260624-001 | COLLAB-partner-001 | RND-diffusion-001
REF_PATTERNS: dict[str, re.Pattern[str]] = {
    "APP": re.compile(
        r"^APP-(?P<slug>[a-z0-9-]+)-(?:(?:F(?P<fseq>\d{3}))|(?P<seq>\d{3}))$",
        re.I,
    ),
    "GDD": re.compile(
        r"^GDD-(?P<scope>WYR|NWA)-(?P<slug>[a-z0-9-]+)-(?P<seq>\d{3})$", re.I
    ),
    "LORE": re.compile(r"^LORE-(?P<scope>WYR|NWA)-(?P<seq>\d{3})$", re.I),
    "ASSET": re.compile(
        r"^ASSET-(?:(?P<scope>WYR)-(?P<subtype>ENV|CHAR|VFX|MAT|SFX)|APP-(?P<app_slug>[a-z0-9-]+))-(?P<seq>\d{3})$",
        re.I,
    ),
    "BUG": re.compile(r"^BUG-(?P<day>\d{8})-(?P<seq>\d{3})$", re.I),
    "COLLAB": re.compile(r"^COLLAB-(?P<slug>[a-z0-9-]+)-(?P<seq>\d{3})$", re.I),
    "RND": re.compile(r"^RND-(?P<slug>[a-z0-9-]+)-(?P<seq>\d{3})$", re.I),
}

_lock = threading.Lock()


@dataclass(frozen=True)
class ParsedRef:
    raw: str
    kind: RefKind
    scope: str | None = None
    slug: str | None = None
    subtype: str | None = None
    day: str | None = None
    seq: int = 0
    counter_key: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "raw": self.raw,
            "kind": self.kind,
            "scope": self.scope,
            "slug": self.slug,
            "subtype": self.subtype,
            "day": self.day,
            "seq": self.seq,
            "counter_key": self.counter_key,
        }


def _slugify(value: str) -> str:
    s = value.strip().lower()
    s = re.sub(r"[^a-z0-9]+", "-", s)
    return s.strip("-")[:48] or "item"


def _load_store() -> dict[str, Any]:
    if not COUNTERS_FILE.exists():
        return {"counters": {}, "issued": []}
    try:
        data = json.loads(COUNTERS_FILE.read_text(encoding="utf-8"))
        if isinstance(data, dict):
            data.setdefault("counters", {})
            data.setdefault("issued", [])
            return data
    except (OSError, json.JSONDecodeError) as exc:
        logger.warning("nomenclature store corrupt, resetting: %s", exc)
    return {"counters": {}, "issued": []}


def _save_store(data: dict[str, Any]) -> None:
    COUNTERS_FILE.parent.mkdir(parents=True, exist_ok=True)
    COUNTERS_FILE.write_text(
        json.dumps(data, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def _counter_key_for(
    kind: RefKind,
    *,
    scope: str | None = None,
    slug: str | None = None,
    subtype: str | None = None,
    day: str | None = None,
    feature: bool = False,
) -> str:
    slug_n = _slugify(slug) if slug else ""
    if kind == "LORE":
        return f"LORE-{(scope or SCOPE_WYR).upper()}"
    if kind == "GDD":
        return f"GDD-{(scope or SCOPE_WYR).upper()}-{slug_n}"
    if kind == "APP":
        return f"APP-{slug_n}{'-F' if feature else ''}"
    if kind == "ASSET":
        if subtype and subtype.upper() == "APP":
            return f"ASSET-APP-{_slugify(slug or 'app')}"
        if slug and not scope:
            return f"ASSET-APP-{_slugify(slug)}"
        return f"ASSET-{(scope or SCOPE_WYR).upper()}-{(subtype or 'ENV').upper()}"
    if kind == "BUG":
        return f"BUG-{day or date.today().strftime('%Y%m%d')}"
    if kind == "COLLAB":
        return f"COLLAB-{slug_n}"
    if kind == "RND":
        return f"RND-{slug_n}"
    raise ValueError(f"Unknown kind: {kind}")


def _format_ref(
    kind: RefKind,
    seq: int,
    *,
    scope: str | None = None,
    slug: str | None = None,
    subtype: str | None = None,
    day: str | None = None,
    feature: bool = False,
) -> str:
    n = f"{seq:03d}"
    if kind == "LORE":
        return f"LORE-{(scope or SCOPE_WYR).upper()}-{n}"
    if kind == "GDD":
        return f"GDD-{(scope or SCOPE_WYR).upper()}-{_slugify(slug or 'doc')}-{n}"
    if kind == "APP":
        mid = f"{_slugify(slug or 'app')}-F{n}" if feature else f"{_slugify(slug or 'app')}-{n}"
        return f"APP-{mid}"
    if kind == "ASSET":
        if subtype and subtype.upper() == "APP":
            return f"ASSET-APP-{_slugify(slug or 'app')}-{n}"
        return f"ASSET-{(scope or SCOPE_WYR).upper()}-{(subtype or 'ENV').upper()}-{n}"
    if kind == "BUG":
        return f"BUG-{day or date.today().strftime('%Y%m%d')}-{n}"
    if kind == "COLLAB":
        return f"COLLAB-{_slugify(slug or 'partner')}-{n}"
    if kind == "RND":
        return f"RND-{_slugify(slug or 'topic')}-{n}"
    raise ValueError(f"Unknown kind: {kind}")


def parse_ref(ref: str) -> ParsedRef | None:
    """Parse and validate a reference string. Returns None if invalid."""
    raw = ref.strip().upper()
    if not raw:
        return None

    for kind, pattern in REF_PATTERNS.items():
        m = pattern.match(raw)
        if not m:
            continue
        gd = m.groupdict()
        seq_raw = gd.get("fseq") or gd.get("seq") or "0"
        seq = int(seq_raw)
        scope = (gd.get("scope") or "").upper() or None
        slug = gd.get("slug") or gd.get("app_slug")
        subtype = (gd.get("subtype") or "").upper() or None
        day = gd.get("day")
        feature = bool(gd.get("fseq"))
        if kind == "ASSET" and gd.get("app_slug"):
            subtype = "APP"
            slug = gd.get("app_slug")

        counter_key = _counter_key_for(
            kind,  # type: ignore[arg-type]
            scope=scope,
            slug=slug,
            subtype=subtype,
            day=day,
            feature=feature,
        )

        return ParsedRef(
            raw=raw,
            kind=kind,  # type: ignore[arg-type]
            scope=scope,
            slug=slug.lower() if slug else None,
            subtype=subtype,
            day=day,
            seq=seq,
            counter_key=counter_key,
        )
    return None


def validate_ref(ref: str) -> bool:
    return parse_ref(ref) is not None


def _bump_counter(store: dict[str, Any], key: str, minimum: int = 0) -> int:
    counters: dict[str, int] = store["counters"]
    current = int(counters.get(key, 0))
    next_val = max(current, minimum) + 1
    counters[key] = next_val
    return next_val


def next_ref(
    kind: RefKind,
    *,
    slug: str | None = None,
    scope: str | None = None,
    subtype: str | None = None,
    day: str | None = None,
    feature: bool = False,
    reserve: bool = True,
) -> str:
    """
    Allocate the next reference ID for a family (increments persisted counter).
    """
    key = _counter_key_for(
        kind,
        scope=scope,
        slug=slug,
        subtype=subtype,
        day=day,
        feature=feature,
    )
    with _lock:
        store = _load_store()
        seq = _bump_counter(store, key)
        ref = _format_ref(
            kind,
            seq,
            scope=scope,
            slug=slug,
            subtype=subtype,
            day=day,
            feature=feature,
        )
        if reserve:
            issued: list[str] = store["issued"]
            if ref not in issued:
                issued.append(ref)
                if len(issued) > 2000:
                    store["issued"] = issued[-2000:]
        _save_store(store)
    return ref


def peek_next_ref(
    kind: RefKind,
    *,
    slug: str | None = None,
    scope: str | None = None,
    subtype: str | None = None,
    day: str | None = None,
    feature: bool = False,
) -> str:
    """Preview next ref without incrementing."""
    key = _counter_key_for(
        kind, scope=scope, slug=slug, subtype=subtype, day=day, feature=feature
    )
    store = _load_store()
    seq = int(store["counters"].get(key, 0)) + 1
    return _format_ref(
        kind, seq, scope=scope, slug=slug, subtype=subtype, day=day, feature=feature
    )


def reconcile_refs(refs: list[str]) -> dict[str, Any]:
    """
    Update counters from an existing ref list (e.g. Obsidian vault scan).
    Sets each counter to the max sequence seen — does not issue new refs.
    """
    updated: dict[str, int] = {}
    parsed_ok = 0
    invalid: list[str] = []

    with _lock:
        store = _load_store()
        counters: dict[str, int] = store["counters"]

        for ref in refs:
            p = parse_ref(ref)
            if not p:
                invalid.append(ref)
                continue
            parsed_ok += 1
            prev = int(counters.get(p.counter_key, 0))
            if p.seq > prev:
                counters[p.counter_key] = p.seq
                updated[p.counter_key] = p.seq

        if updated:
            _save_store(store)

    counters_out = _load_store()["counters"]
    return {
        "parsed": parsed_ok,
        "invalid": invalid,
        "counters_updated": updated,
        "counters": dict(counters_out),
    }


def reconcile_vault(vault: Path | None = None) -> dict[str, Any]:
    """Scan Obsidian vault notes and sync counters."""
    from services.obsidian_vault import get_vault_path, list_notes

    root = vault or get_vault_path()
    refs: list[str] = []
    for note in list_notes(vault=root):
        if note.ref:
            refs.append(note.ref)
    # Also catch refs in filenames
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
