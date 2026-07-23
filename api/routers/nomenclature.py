"""Nomenclature API — reference ID generation and validation."""

from __future__ import annotations

from api.route_common import *  # noqa: F403

router = APIRouter(prefix="/nomenclature", tags=["nomenclature"])

_VALID_KINDS = frozenset({"APP", "GDD", "LORE", "ASSET", "BUG", "COLLAB", "RND"})


@router.get("/counters")
def nomenclature_counters() -> dict[str, Any]:
    from services.nomenclature import _load_store

    store = _load_store()
    return {"counters": store.get("counters", {}), "issued_count": len(store.get("issued", []))}


@router.post("/next")
def nomenclature_next(body: NomenclatureNextRequest) -> dict[str, Any]:
    from services.nomenclature import create_obsidian_stub, next_ref, parse_ref, suggest_obsidian_path

    kind = body.kind.strip().upper()
    if kind not in _VALID_KINDS:
        raise HTTPException(status_code=400, detail=f"Invalid kind: {body.kind}")

    ref = next_ref(
        kind,  # type: ignore[arg-type]
        slug=body.slug,
        scope=body.scope,
        subtype=body.subtype,
        feature=body.feature,
    )
    out: dict[str, Any] = {
        "ref": ref,
        "parsed": parse_ref(ref).to_dict() if parse_ref(ref) else None,
        "suggested_path": suggest_obsidian_path(ref),
    }
    if body.create_note:
        out["note"] = create_obsidian_stub(ref, title=body.title)
    return out


@router.get("/peek")
def nomenclature_peek(
    kind: str,
    slug: str | None = None,
    scope: str | None = None,
    subtype: str | None = None,
    feature: bool = False,
) -> dict[str, Any]:
    from services.nomenclature import peek_next_ref, suggest_obsidian_path

    k = kind.strip().upper()
    if k not in _VALID_KINDS:
        raise HTTPException(status_code=400, detail=f"Invalid kind: {kind}")
    ref = peek_next_ref(
        k,  # type: ignore[arg-type]
        slug=slug,
        scope=scope,
        subtype=subtype,
        feature=feature,
    )
    return {"ref": ref, "suggested_path": suggest_obsidian_path(ref)}


@router.post("/validate")
def nomenclature_validate(body: NomenclatureValidateRequest) -> dict[str, Any]:
    from services.nomenclature import parse_ref, suggest_obsidian_path

    parsed = parse_ref(body.ref)
    return {
        "valid": parsed is not None,
        "parsed": parsed.to_dict() if parsed else None,
        "suggested_path": suggest_obsidian_path(body.ref) if parsed else None,
    }


@router.post("/reconcile")
def nomenclature_reconcile() -> dict[str, Any]:
    """Scan Obsidian vault and align counters with existing refs."""
    from services.nomenclature import reconcile_vault

    return reconcile_vault()
