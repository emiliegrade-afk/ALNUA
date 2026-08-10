"""Allocate and reconcile ALNUA reference ID counters."""

from __future__ import annotations

from typing import Any

from services.nomenclature_constants import RefKind, _lock
from services.nomenclature_parse import parse_ref
from services.nomenclature_store import (
    _bump_counter,
    _counter_key_for,
    _format_ref,
    _load_store,
    _save_store,
)


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
