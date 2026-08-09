"""Hub CRUD — peeled from core.py (debt paydown)."""

from __future__ import annotations

from api.route_common import *  # noqa: F403

router = APIRouter()

@router.get("/gaming/community-stats")
def gaming_community_stats() -> dict[str, Any]:
    """Steam (joueurs simultanés) + Discord (membres) — Phase 18, ROADMAP.md.

    Wishlist Steam volontairement absent : Valve n'expose pas ce chiffre via
    une API publique (accès Steamworks Partner requis) — voir skill_steam.py.
    """
    from skills.skill_discord_wyrdheim import discord_is_configured, get_member_count
    from skills.skill_steam import get_concurrent_players, steam_is_configured

    return {
        "steam_configured": steam_is_configured(),
        "steam_concurrent_players": get_concurrent_players(),
        "discord_configured": discord_is_configured(),
        "discord_member_count": get_member_count(),
    }


@router.get("/gaming/assets")
def list_gaming_assets(project_id: str | None = None, category: str | None = None) -> list[dict[str, Any]]:
    db = get_supabase()
    filters: dict[str, Any] = {}
    if project_id:
        filters["project_id"] = project_id
    if category:
        filters["category"] = category
    return db.select("gaming_assets", filters=filters or None, order_by="category")


@router.post("/gaming/assets/sync")
def sync_gaming_assets(body: GamingAssetsSync) -> dict[str, Any]:
    """Remplace l'inventaire d'assets d'un projet par l'état actuel scanné localement.

    Chaque appel reflète l'état du dossier au moment du scan — voir
    scripts/sync_ue5_assets.py. Les anciennes lignes du projet sont purgées
    avant d'insérer le nouveau lot.
    """
    db = get_supabase()
    existing = db.select("gaming_assets", filters={"project_id": body.project_id})
    for row in existing:
        db.delete("gaming_assets", row["id"])

    if not body.assets:
        return {"project_id": body.project_id, "synced": 0}

    rows = [
        {
            "project_id": body.project_id,
            "category": a.category,
            "name": a.name,
            "asset_type": a.asset_type,
            "file_path": a.file_path,
            "size_bytes": a.size_bytes,
            "modified_at": a.modified_at.isoformat() if a.modified_at else None,
        }
        for a in body.assets
    ]
    inserted = db.insert_many("gaming_assets", rows)
    return {"project_id": body.project_id, "synced": len(inserted)}


@router.get("/gaming/builds")
def list_gaming_builds(project_id: str | None = None, limit: int = Query(default=20, le=100)) -> list[dict[str, Any]]:
    db = get_supabase()
    filters: dict[str, Any] = {}
    if project_id:
        filters["project_id"] = project_id
    return db.select(
        "gaming_builds",
        filters=filters or None,
        order_by="created_at",
        ascending=False,
        limit=limit,
    )


@router.post("/gaming/builds")
def create_gaming_build(body: GamingBuildCreate) -> dict[str, Any]:
    db = get_supabase()
    return db.insert(
        "gaming_builds",
        {
            "project_id": body.project_id,
            "branch": body.branch,
            "build_number": body.build_number,
            "game_version": body.game_version,
            "engine_version": body.engine_version,
            "status": body.status,
            "fps_avg": body.fps_avg,
            "crashes": body.crashes,
            "draw_calls": body.draw_calls,
            "commit_sha": body.commit_sha,
            "notes": body.notes,
        },
    )


