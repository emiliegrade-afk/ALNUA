"""Promote hypothesis-tree nodes to R&D dossiers."""

from __future__ import annotations

import logging
from typing import Any

from services.rnd_hypothesis_tree_helpers import (
    _load_tree,
    _node,
    _patch_idea_fields,
    _save_tree,
    _utc_now,
)

logger = logging.getLogger(__name__)


def promote_node_to_dossier(slug: str, node_id: str, *, enrich: bool = True) -> dict[str, Any]:
    """Create idea (if needed) + promote to R&D dossier in one step."""
    import services.rnd_hypothesis_tree as facade

    tree = _load_tree(slug)
    if not tree:
        raise ValueError("Arbre introuvable")
    node = _node(tree, node_id)

    if node.get("dossier_id"):
        return {
            "success": True,
            "already": True,
            "dossier_id": node["dossier_id"],
            "idea_id": node.get("idea_id"),
            "message": "Dossier déjà créé pour cette branche.",
        }

    from agents.rnd_center import inject_idea
    from agents.rnd_dossier_agent import promote_idea_to_dossier

    idea_id = node.get("idea_id")
    if not idea_id:
        findings = node.get("evidence", {}).get("key_findings") or []
        findings_text = "\n".join(f"- {f}" for f in findings[:5])
        body = (
            f"{node.get('title', 'Concept R&D')}\n\n"
            f"{node.get('hypothesis', '')}\n\n"
            f"Insight arbre : {node.get('insight', '')}\n\n"
            f"Findings :\n{findings_text}"
        ).strip()
        idea = inject_idea(body[:2000], source=f"hypothesis_tree:{slug}")
        idea_id = idea.get("id")
        node["idea_id"] = idea_id
        if node.get("score") is not None:
            _patch_idea_fields(
                idea_id,
                {
                    "score": node["score"],
                    "verdict": node.get("verdict") or "MAYBE",
                    "status": "evaluated_go" if node.get("verdict") == "GO" else "evaluated_maybe",
                    "title": node.get("title", idea.get("title")),
                    "description": body[:2000],
                },
            )

    if not idea_id:
        raise RuntimeError("Impossible de créer l'idée R&D")

    result = promote_idea_to_dossier(str(idea_id), actor="emilie", enrich=False)
    dossier_id = result["dossier"]["id"]
    node["dossier_id"] = dossier_id
    if node.get("status") not in ("merged", "pruned"):
        node["status"] = "merged"
    node["updated_at"] = _utc_now()
    tree["updated_at"] = _utc_now()
    _save_tree(tree)

    if enrich:
        from agents.rnd_dossier_agent import RndDossierAgent

        def _enrich_bg() -> None:
            try:
                RndDossierAgent().enrich_dossier(dossier_id, actor="rnd_dossier_agent")
            except Exception:
                logger.exception("enrich after tree promote failed")

        facade.threading.Thread(target=_enrich_bg, daemon=True).start()
        result["enriching"] = True
        result["message"] = (
            f"Dossier « {result['dossier']['title']} » créé — enrichissement en cours (30–60 s)."
        )
    else:
        result["enriching"] = False

    result["success"] = True
    result["idea_id"] = idea_id
    result["dossier_id"] = dossier_id
    result["tree_slug"] = slug
    result["node_id"] = node_id
    return result
