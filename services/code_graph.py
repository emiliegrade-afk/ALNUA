"""
services/code_graph.py — Graphe de connaissance du codebase ALNUA.

Inspiré de graphify (⭐1.1k) — transforme code/SQL/docs en graphe queryable.
Axel (analyst_data) utilise ce service pour naviguer l'architecture sans lire
chaque fichier. Idris (brainstorm) l'utilise pour générer des idées connectées.

Nœuds : fichiers, classes, fonctions, endpoints, agents, schemas, tables
Arêtes : imports, calls, inherits, defines, exposes

Usage:
    from services.code_graph import query_graph, get_agent_context, get_codebase_summary

    summary = get_codebase_summary()
    ctx = get_agent_context("dev_backend")
    result = query_graph("Quels agents utilisent Supabase directement ?")
"""
from __future__ import annotations

from services.code_graph_models import CodeGraph, GraphEdge, GraphNode  # noqa: F401 — re-export
from services.code_graph_query import (  # noqa: F401 — re-export
    get_agent_context,
    get_codebase_summary,
    invalidate_cache,
    query_graph,
)

__all__ = [
    "CodeGraph",
    "GraphEdge",
    "GraphNode",
    "get_agent_context",
    "get_codebase_summary",
    "invalidate_cache",
    "query_graph",
]
