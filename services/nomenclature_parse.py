"""Parse and validate ALNUA reference ID strings."""

from __future__ import annotations

from services.nomenclature_constants import REF_PATTERNS, ParsedRef
from services.nomenclature_store import _counter_key_for


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
