"""R&D hypothesis trees + LLM latency benchmark routes (split from rnd.py — Phase D).
"""

from __future__ import annotations

from api.route_common import *  # noqa: F403

router = APIRouter()


@router.get("/rnd/trees")
def rnd_list_trees(limit: int = Query(default=20, le=50)) -> dict[str, Any]:
    from services.rnd_hypothesis_tree import list_trees

    return {"trees": list_trees(limit=limit)}


@router.get("/rnd/trees/{slug}")
def rnd_get_tree(slug: str) -> dict[str, Any]:
    from services.rnd_hypothesis_tree import get_tree

    tree = get_tree(slug)
    if not tree:
        raise HTTPException(status_code=404, detail="Arbre introuvable")
    return tree


@router.get("/rnd/watch-topics")
def rnd_watch_topics() -> dict[str, Any]:
    from services.rnd_hypothesis_tree import get_watch_topics

    return {"topics": get_watch_topics()}


@router.get("/rnd/trees/{slug}/graph")
def rnd_tree_graph(slug: str) -> dict[str, Any]:
    from services.rnd_hypothesis_tree import build_tree_graph

    graph = build_tree_graph(slug)
    if not graph:
        raise HTTPException(status_code=404, detail="Arbre introuvable")
    return graph


@router.post("/rnd/trees/{slug}/nodes/{node_id}/expand")
def rnd_expand_node(
    slug: str,
    node_id: str,
    body: dict[str, Any] | None = None,
) -> dict[str, Any]:
    req = body or {}
    try:
        from services.rnd_hypothesis_tree import expand_node

        manual = None
        if req.get("title"):
            manual = {
                "title": str(req["title"])[:200],
                "hypothesis": str(req.get("hypothesis") or req["title"])[:2000],
            }
        return expand_node(
            slug,
            node_id,
            max_children=int(req.get("max_children") or 3),
            run_after=bool(req.get("run_after")),
            manual=manual,
        )
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except Exception as exc:
        logger.exception("rnd_expand_node failed")
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.post("/rnd/trees/{slug}/nodes/{node_id}/run")
def rnd_run_node(slug: str, node_id: str) -> dict[str, Any]:
    try:
        from services.rnd_hypothesis_tree import run_node

        return run_node(slug, node_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.patch("/rnd/trees/{slug}/nodes/{node_id}")
def rnd_patch_node(slug: str, node_id: str, body: dict[str, Any]) -> dict[str, Any]:
    status = str(body.get("status") or "").strip()
    if not status:
        raise HTTPException(status_code=400, detail="status requis")
    try:
        from services.rnd_hypothesis_tree import set_node_status

        return set_node_status(slug, node_id, status)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.patch("/rnd/trees/{slug}/nodes/{node_id}/reparent")
def rnd_reparent_node(slug: str, node_id: str, body: dict[str, Any]) -> dict[str, Any]:
    """Glisser un nœud sur un autre dans le canvas Arbres (Phase 26, ROADMAP.md) = "relier"."""
    new_parent_id = str(body.get("new_parent_id") or "").strip()
    if not new_parent_id:
        raise HTTPException(status_code=400, detail="new_parent_id requis")
    try:
        from services.rnd_hypothesis_tree import reparent_node

        return reparent_node(slug, node_id, new_parent_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        logger.exception("rnd_reparent_node failed")
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.post("/rnd/trees/{slug}/nodes/{node_id}/promote")
def rnd_promote_tree_node(
    slug: str,
    node_id: str,
    enrich: bool = Query(default=True, alias="enrich"),
) -> dict[str, Any]:
    try:
        from services.rnd_hypothesis_tree import promote_node_to_dossier

        return promote_node_to_dossier(slug, node_id, enrich=enrich)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except Exception as exc:
        logger.exception("rnd_promote_tree_node failed")
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.post("/rnd/benchmark/llm-latency")
def rnd_run_llm_benchmark(body: dict[str, Any] | None = None) -> dict[str, Any]:
    """Benchmark OpenRouter vs DiffusionGemma reference on short Hub tasks."""
    req = body or {}
    try:
        from services.rnd_llm_benchmark import run_llm_latency_benchmark

        return run_llm_latency_benchmark(
            agent_id=str(req.get("agent_id") or "secretary"),
            prompts=req.get("prompts"),
        )
    except Exception as exc:
        logger.exception("rnd_run_llm_benchmark failed")
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.get("/rnd/benchmark/llm-latency/latest")
def rnd_latest_llm_benchmark() -> dict[str, Any]:
    from services.rnd_llm_benchmark import get_latest_benchmark

    latest = get_latest_benchmark()
    if not latest:
        return {"benchmark": None, "message": "Aucun benchmark — lance POST /rnd/benchmark/llm-latency"}
    return {"benchmark": latest}

