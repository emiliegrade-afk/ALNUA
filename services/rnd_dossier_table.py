"""Vue table Dossiers (Phase 27, ROADMAP.md) — read model qui pré-joint
idée (score/verdict), vote Conseil (Phase 25), documents et section marché
sur chaque dossier, pour éviter un N+1 de requêtes côté frontend (12+
dossiers réels × plusieurs appels chacun).

Les idées/documents/sessions comité sont chacun récupérés en UN seul appel
(tables encore petites, pas de filtre `.in_` disponible côté
`SupabaseClient.select` — voir database/supabase_client.py) puis indexés en
Python, plutôt qu'un appel par dossier : divise le temps de chargement par
~2 par rapport à une version naïve entièrement par-dossier (mesuré en live,
Phase 27 : ~14.5s → ~7s sur 12 dossiers réels). `repo.get_dossier(id)` reste
appelé par dossier (agrège sections/committee_team/statut CEO — dupliquer
cette logique juste pour gagner quelques secondes de plus serait hors
périmètre de cette phase)."""

from __future__ import annotations

from typing import Any

from services.rnd_repository import get_rnd_repository

MARKET_EXCERPT_LEN = 220


def _prototype_label(dispatch_status: str, project_id: str | None) -> str | None:
    if project_id:
        return "Projet réel dispatché"
    if dispatch_status == "dispatched":
        return "Dispatché"
    return None


def _council_verdict_from_sessions(
    db: Any,
    idea_id: str,
    sessions_by_idea: dict[str, list[dict[str, Any]]],
) -> dict[str, Any] | None:
    """Dernière session Conseil (stratégique/évaluation) close pour cette
    idée — les sessions comité classiques ('dossier') n'ont pas de vote
    structuré (Phase 25 n'a ajouté rnd_committee_votes qu'au Conseil)."""
    candidates = [
        s
        for s in sessions_by_idea.get(idea_id, [])
        if s.get("status") == "closed" and s.get("session_kind") in ("evaluation", "strategic")
    ]
    if not candidates:
        return None
    session = max(candidates, key=lambda s: s.get("closed_at") or "")

    votes = db.select(
        "rnd_committee_votes",
        filters={"session_id": session["session_id"]},
        order_by="round_index",
    )
    if not votes:
        return None
    latest: dict[str, dict[str, Any]] = {}
    for v in votes:
        latest[v["agent_id"]] = v
    counts: dict[str, int] = {}
    for v in latest.values():
        counts[v["verdict"]] = counts.get(v["verdict"], 0) + 1
    if not counts:
        return None
    recommendation = max(counts, key=lambda k: counts[k])
    consensus_pct = round(100 * counts[recommendation] / len(latest))
    return {"verdict": recommendation, "consensus_pct": consensus_pct, "votes_count": len(latest)}


def build_dossier_table_rows(
    *,
    status: str | None = None,
    domain: str | None = None,
    limit: int = 50,
) -> list[dict[str, Any]]:
    repo = get_rnd_repository()
    base_items = repo.list_dossiers(status=status, domain=domain, limit=limit)

    ideas_by_id = {row["id"]: row for row in (repo.db.select("rnd_ideas", limit=500) or [])}
    assets_by_dossier: dict[str, int] = {}
    for row in repo.db.select("rnd_dossier_assets", limit=1000) or []:
        did = row.get("dossier_id")
        if did:
            assets_by_dossier[did] = assets_by_dossier.get(did, 0) + 1
    sessions_by_idea: dict[str, list[dict[str, Any]]] = {}
    for row in repo.db.select("rnd_committee_sessions", limit=500) or []:
        iid = row.get("idea_id")
        if iid:
            sessions_by_idea.setdefault(iid, []).append(row)

    rows: list[dict[str, Any]] = []
    for item in base_items:
        dossier = repo.get_dossier(item.id)
        if not dossier:
            continue

        idea_row = ideas_by_id.get(dossier.idea_id)
        market_section = next(
            (s for s in dossier.sections if s.section_key == "market" and s.content_md.strip()),
            None,
        )
        votes = _council_verdict_from_sessions(repo.db, dossier.idea_id, sessions_by_idea)

        rows.append(
            {
                "id": dossier.id,
                "slug": dossier.slug,
                "title": dossier.title,
                "tagline": dossier.tagline,
                "domain": dossier.domain,
                "branch": dossier.branch,
                "status": dossier.status,
                "ceo_status": dossier.ceo_status,
                "ceo_note": dossier.ceo_note,
                "updated_at": dossier.updated_at,
                # idea_legacy_id : nécessaire pour rouvrir ce dossier dans
                # DossierDetailView (rnd-v2/dossier-detail-view.tsx, Phase 23)
                # côté frontend — "Incuber"/"Supprimer" y opèrent sur l'idée,
                # pas le dossier.
                "idea_legacy_id": (
                    (idea_row.get("legacy_id") or str(idea_row.get("id", ""))) if idea_row else None
                ),
                "score": idea_row.get("score") if idea_row else None,
                "verdict": idea_row.get("agent_verdict") if idea_row else None,
                "market_score": idea_row.get("market_score") if idea_row else None,
                "feasibility_score": idea_row.get("feasibility_score") if idea_row else None,
                "vision_score": idea_row.get("vision_score") if idea_row else None,
                "incubator_stage": (idea_row.get("incubator_stage") or "idee") if idea_row else "idee",
                "agents_count": len(dossier.committee_team),
                "votes": votes,
                "documents_count": assets_by_dossier.get(dossier.id, 0),
                "market_excerpt": (
                    market_section.content_md.strip()[:MARKET_EXCERPT_LEN] if market_section else None
                ),
                "prototype_label": _prototype_label(dossier.dispatch_status, dossier.project_id),
            }
        )

    return rows
