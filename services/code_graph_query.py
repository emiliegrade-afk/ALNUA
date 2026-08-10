"""In-memory cache and query interface for the ALNUA code graph."""

from __future__ import annotations

import json
import logging
import time
from typing import Any

from services.code_graph_build import build_graph
from services.code_graph_models import CodeGraph

logger = logging.getLogger(__name__)

_GRAPH_CACHE: CodeGraph | None = None
_CACHE_TTL = 300  # 5 min

_GRAPH_QUERY_SYSTEM = """Tu es Axel Roux, Data Analyst ALNUA.
Tu réponds à des questions sur l'architecture du codebase ALNUA en analysant
le contexte graphe fourni.
Sois précis, cite les nœuds et relations pertinents.
Réponds en JSON valide."""


def get_or_build_graph(*, rebuild: bool = False) -> CodeGraph:
    global _GRAPH_CACHE
    if rebuild:
        _GRAPH_CACHE = None
    if _GRAPH_CACHE is None or (time.time() - _GRAPH_CACHE.built_at) > _CACHE_TTL:
        _GRAPH_CACHE = build_graph()
    return _GRAPH_CACHE


def invalidate_cache() -> dict[str, str]:
    """Force rebuild du graphe au prochain appel."""
    global _GRAPH_CACHE
    _GRAPH_CACHE = None
    return {"status": "cache invalidated"}


def query_graph(
    question: str,
    agent_id: str = "analyst_data",
    rebuild: bool = False,
) -> dict[str, Any]:
    """
    Répond à une question sur l'architecture en langage naturel.

    Endpoint: POST /services/code-graph/query
    """
    graph = get_or_build_graph(rebuild=rebuild)

    graph_context = {
        "summary": graph.to_summary_dict(),
        "agents": [n.to_dict() for n in graph.find_nodes("agent")],
        "endpoints": [n.to_dict() for n in graph.find_nodes("endpoint")][:50],
        "files": [n.to_dict() for n in graph.find_nodes("file") if "agents/" in (n.path or "")][:30],
        "tables": [n.to_dict() for n in graph.find_nodes("table")],
    }

    try:
        from agents.base import LLMClient, parse_json_response
        from skills.skill_agent_learning import inject_learning_context

        llm = LLMClient()
        prompt = inject_learning_context(
            f"""QUESTION : {question}

GRAPHE CODEBASE :
{json.dumps(graph_context, ensure_ascii=False, indent=2)[:6000]}

Réponds avec :
- answer (string): réponse directe et précise
- relevant_nodes (list): IDs des nœuds impliqués
- confidence (float 0-1): niveau de confiance
- suggested_follow_ups (list[str]): 2-3 questions de suivi utiles""",
            agent_id, question
        )
        raw = llm.complete(_GRAPH_QUERY_SYSTEM, prompt, agent_id=agent_id, temperature=0.2)
        result = parse_json_response(raw)
    except Exception as e:
        logger.debug("code_graph query LLM failed: %s", e)
        result = {
            "answer": f"Erreur LLM: {e}",
            "relevant_nodes": [],
            "confidence": 0.0,
            "suggested_follow_ups": [],
        }

    return {
        "question": question,
        "agent_id": agent_id,
        "graph_stats": graph.to_summary_dict(),
        **result,
    }


def get_agent_context(agent_id: str) -> dict[str, Any]:
    """
    Retourne tout le contexte graphe pertinent pour un agent donné.

    Endpoint: GET /services/code-graph/agent/{agent_id}
    """
    graph = get_or_build_graph()

    agent_node_id = f"agent::{agent_id}"
    agent_file = f"agents/{agent_id}_agent.py"

    node = graph.nodes.get(agent_node_id) or graph.nodes.get(agent_file)
    if not node:
        return {"error": f"Agent '{agent_id}' not found in graph", "agent_id": agent_id}

    imports = graph.neighbors(agent_file, "imports")
    defines = graph.neighbors(agent_file, "defines")

    endpoints = [
        n.to_dict() for n in graph.find_nodes("endpoint")
        if agent_id.replace("_", "-") in n.label.lower()
        or agent_id in n.label.lower()
    ]

    tables = graph.neighbors(agent_file, "uses")

    return {
        "agent_id": agent_id,
        "agent_node": node.to_dict(),
        "imports": [n.to_dict() for n in imports],
        "defines": [n.to_dict() for n in defines],
        "endpoints": endpoints,
        "tables": [n.to_dict() for n in tables],
        "graph_stats": graph.to_summary_dict(),
    }


def get_codebase_summary(rebuild: bool = False) -> dict[str, Any]:
    """
    Vue d'ensemble complète du codebase sous forme de graphe.

    Endpoint: GET /services/code-graph/summary
    """
    graph = get_or_build_graph(rebuild=rebuild)

    import_counts: dict[str, int] = {}
    for e in graph.edges:
        if e.relation == "imports":
            import_counts[e.target] = import_counts.get(e.target, 0) + 1

    top_files = sorted(import_counts.items(), key=lambda x: x[1], reverse=True)[:10]

    return {
        "summary": graph.to_summary_dict(),
        "agents": [n.to_dict() for n in graph.find_nodes("agent")],
        "endpoints_count": len(graph.find_nodes("endpoint")),
        "endpoints_sample": [n.to_dict() for n in graph.find_nodes("endpoint")][:20],
        "tables": [n.to_dict() for n in graph.find_nodes("table")],
        "top_imported_files": [
            {"file": f, "import_count": c} for f, c in top_files
        ],
        "built_at": graph.built_at,
    }
