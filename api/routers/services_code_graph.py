"""Advanced services — Code Graph + Memory Compression (peeled from advanced_services.py)."""

from __future__ import annotations

from api.route_common import *  # noqa: F403

router = APIRouter(prefix="/services", tags=["advanced-services"])


class CodeGraphQueryRequest(BaseModel):
    question: str
    agent_id: str = "analyst_data"
    rebuild: bool = False


@router.post("/code-graph/query")
def code_graph_query(body: CodeGraphQueryRequest) -> dict[str, Any]:
    """
    Répond à une question sur l'architecture du codebase en langage naturel.
    Axel (analyst_data) analyse le graphe et répond avec les nœuds pertinents.
    """
    from services.code_graph import query_graph
    return query_graph(body.question, body.agent_id, body.rebuild)


@router.get("/code-graph/summary")
def code_graph_summary(rebuild: bool = False) -> dict[str, Any]:
    """
    Vue d'ensemble du codebase : agents, endpoints, tables, fichiers les plus importés.
    """
    from services.code_graph import get_codebase_summary
    return get_codebase_summary(rebuild)


@router.get("/code-graph/agent/{agent_id}")
def code_graph_agent(agent_id: str) -> dict[str, Any]:
    """
    Contexte complet d'un agent dans le graphe :
    imports, méthodes définies, endpoints associés, tables utilisées.
    """
    from services.code_graph import get_agent_context
    return get_agent_context(agent_id)


@router.post("/code-graph/invalidate")
def code_graph_invalidate() -> dict[str, str]:
    """Force le rebuild du graphe au prochain appel (cache invalidé)."""
    from services.code_graph import invalidate_cache
    return invalidate_cache()


class MemoryCompressRequest(BaseModel):
    agent_id: str
    threshold: int = 20


@router.post("/memory/compress")
def memory_compress(body: MemoryCompressRequest) -> dict[str, Any]:
    """
    Compresse les mémoires d'un agent si elles dépassent le seuil.
    Distille N leçons brutes → 3-5 règles comportementales durables.
    """
    from skills.skill_agent_learning import auto_compress_if_needed
    compressed = auto_compress_if_needed(body.agent_id, body.threshold, blocking=True)
    return {
        "agent_id": body.agent_id,
        "compressed": compressed,
        "message": "Compression lancée" if compressed else "Pas de compression nécessaire",
    }
