"""
services/code_graph.py — Graphe de connaissance du codebase ALNUA.

Inspiré de graphify (⭐1.1k) — transforme code/SQL/docs en graphe queryable.
Axel (analyst_data) utilise ce service pour naviguer l'architecture sans lire
chaque fichier. Idris (brainstorm) l'utilise pour générer des idées connectées.

Nœuds : fichiers, classes, fonctions, endpoints, agents, schemas, tables
Arêtes : imports, calls, inherits, defines, exposes

Usage:
    from services.code_graph import query_graph, get_agent_context, get_codebase_summary

    # Résumé architecture complète
    summary = get_codebase_summary()

    # Contexte agent spécifique
    ctx = get_agent_context("dev_backend")  # tout ce que sait Hao Chen

    # Query en langage naturel
    result = query_graph("Quels agents utilisent Supabase directement ?")
"""
from __future__ import annotations

import ast
import json
import logging
import os
import re
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

# Répertoire racine du projet (relatif à ce fichier : services/ → root)
_PROJECT_ROOT = Path(__file__).parent.parent

# Fichiers et répertoires à ignorer
_IGNORE_DIRS = {
    "__pycache__", ".git", "node_modules", ".venv", "venv",
    "build", "dist", ".next", ".claude", "data",
}
_IGNORE_FILES = {"__init__.py"}


# ---------------------------------------------------------------------------
# Dataclasses graphe
# ---------------------------------------------------------------------------

@dataclass
class GraphNode:
    node_id: str           # Ex: "agents/dev_backend_agent.py::DevBackendAgent"
    node_type: str         # file | class | function | endpoint | agent | schema | table
    label: str             # Nom court
    path: str | None       # Chemin relatif si fichier
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.node_id,
            "type": self.node_type,
            "label": self.label,
            "path": self.path,
            **self.metadata,
        }


@dataclass
class GraphEdge:
    source: str
    target: str
    relation: str   # imports | calls | defines | exposes | inherits | uses

    def to_dict(self) -> dict[str, Any]:
        return {"source": self.source, "target": self.target, "relation": self.relation}


@dataclass
class CodeGraph:
    nodes: dict[str, GraphNode] = field(default_factory=dict)
    edges: list[GraphEdge] = field(default_factory=list)
    built_at: float = field(default_factory=time.time)

    def add_node(self, node: GraphNode) -> None:
        self.nodes[node.node_id] = node

    def add_edge(self, source: str, target: str, relation: str) -> None:
        if source in self.nodes and target in self.nodes:
            self.edges.append(GraphEdge(source=source, target=target, relation=relation))

    def neighbors(self, node_id: str, relation: str | None = None) -> list[GraphNode]:
        """Retourne les nœuds adjacents (sortants)."""
        targets = [
            e.target for e in self.edges
            if e.source == node_id and (relation is None or e.relation == relation)
        ]
        return [self.nodes[t] for t in targets if t in self.nodes]

    def predecessors(self, node_id: str, relation: str | None = None) -> list[GraphNode]:
        """Retourne les nœuds qui pointent vers node_id."""
        sources = [
            e.source for e in self.edges
            if e.target == node_id and (relation is None or e.relation == relation)
        ]
        return [self.nodes[s] for s in sources if s in self.nodes]

    def find_nodes(self, node_type: str | None = None, label_contains: str | None = None) -> list[GraphNode]:
        result = list(self.nodes.values())
        if node_type:
            result = [n for n in result if n.node_type == node_type]
        if label_contains:
            result = [n for n in result if label_contains.lower() in n.label.lower()]
        return result

    def to_summary_dict(self) -> dict[str, Any]:
        type_counts: dict[str, int] = {}
        for n in self.nodes.values():
            type_counts[n.node_type] = type_counts.get(n.node_type, 0) + 1
        relation_counts: dict[str, int] = {}
        for e in self.edges:
            relation_counts[e.relation] = relation_counts.get(e.relation, 0) + 1
        return {
            "total_nodes": len(self.nodes),
            "total_edges": len(self.edges),
            "node_types": type_counts,
            "relation_types": relation_counts,
        }


# ---------------------------------------------------------------------------
# Cache en mémoire (rebuild si > 5 minutes)
# ---------------------------------------------------------------------------

_GRAPH_CACHE: CodeGraph | None = None
_CACHE_TTL = 300  # 5 min


def _get_or_build_graph() -> CodeGraph:
    global _GRAPH_CACHE
    if _GRAPH_CACHE is None or (time.time() - _GRAPH_CACHE.built_at) > _CACHE_TTL:
        _GRAPH_CACHE = _build_graph()
    return _GRAPH_CACHE


# ---------------------------------------------------------------------------
# Builder — parcourt le codebase Python
# ---------------------------------------------------------------------------

def _build_graph() -> CodeGraph:
    """Construit le graphe en parsant les fichiers Python du projet."""
    graph = CodeGraph()
    logger.info("Building code graph...")
    start = time.time()

    python_files = _collect_python_files()

    # Passe 1 : créer les nœuds fichiers + classes + fonctions
    for rel_path, abs_path in python_files:
        file_id = rel_path
        graph.add_node(GraphNode(
            node_id=file_id, node_type="file",
            label=Path(rel_path).name, path=rel_path,
        ))
        try:
            _parse_python_file(graph, abs_path, rel_path)
        except Exception as e:
            logger.debug(f"Parse error {rel_path}: {e}")

    # Passe 2 : déduire les nœuds agents depuis config
    _add_agent_nodes(graph)

    # Passe 3 : endpoints depuis les routers
    _add_endpoint_nodes(graph)

    # Passe 4 : tables Supabase depuis les queries dans le code
    _add_table_hints(graph)

    logger.info(f"Graph built in {int((time.time() - start)*1000)}ms — "
                f"{len(graph.nodes)} nodes, {len(graph.edges)} edges")
    return graph


def _collect_python_files() -> list[tuple[str, Path]]:
    """Retourne (chemin relatif, chemin absolu) pour tous les .py du projet."""
    result = []
    for py_file in _PROJECT_ROOT.rglob("*.py"):
        parts = py_file.relative_to(_PROJECT_ROOT).parts
        if any(p in _IGNORE_DIRS for p in parts):
            continue
        if py_file.name in _IGNORE_FILES:
            continue
        rel = str(py_file.relative_to(_PROJECT_ROOT)).replace("\\", "/")
        result.append((rel, py_file))
    return result


def _parse_python_file(graph: CodeGraph, abs_path: Path, rel_path: str) -> None:
    """Parse un fichier Python avec ast et extrait classes/fonctions/imports."""
    source = abs_path.read_text(encoding="utf-8", errors="ignore")
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return

    file_id = rel_path

    for node in ast.walk(tree):
        # Classes
        if isinstance(node, ast.ClassDef):
            class_id = f"{file_id}::{node.name}"
            graph.add_node(GraphNode(
                node_id=class_id, node_type="class",
                label=node.name, path=rel_path,
                metadata={"lineno": node.lineno},
            ))
            graph.add_edge(file_id, class_id, "defines")

            # Méthodes de la classe
            for item in node.body:
                if isinstance(item, ast.FunctionDef):
                    method_id = f"{class_id}.{item.name}"
                    graph.add_node(GraphNode(
                        node_id=method_id, node_type="function",
                        label=f"{node.name}.{item.name}", path=rel_path,
                        metadata={"lineno": item.lineno},
                    ))
                    graph.add_edge(class_id, method_id, "defines")

            # Héritage
            for base in node.bases:
                if isinstance(base, ast.Name):
                    graph.add_edge(class_id, base.id, "inherits")

        # Fonctions de module
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if not isinstance(node, ast.ClassDef):
                func_id = f"{file_id}::{node.name}"
                if func_id not in graph.nodes:
                    graph.add_node(GraphNode(
                        node_id=func_id, node_type="function",
                        label=node.name, path=rel_path,
                        metadata={"lineno": node.lineno},
                    ))
                    graph.add_edge(file_id, func_id, "defines")

        # Imports
        elif isinstance(node, ast.Import):
            for alias in node.names:
                _add_import_edge(graph, file_id, alias.name)

        elif isinstance(node, ast.ImportFrom):
            if node.module:
                _add_import_edge(graph, file_id, node.module)


def _add_import_edge(graph: CodeGraph, file_id: str, module: str) -> None:
    """Convertit un import en arête s'il pointe vers un fichier du projet."""
    # Ex: "agents.base" → "agents/base.py"
    candidate = module.replace(".", "/") + ".py"
    if candidate in graph.nodes:
        graph.add_edge(file_id, candidate, "imports")


def _add_agent_nodes(graph: CodeGraph) -> None:
    """Crée des nœuds 'agent' depuis config/agent_personas.py si dispo."""
    try:
        personas_path = _PROJECT_ROOT / "config" / "agent_personas.py"
        if not personas_path.exists():
            return
        source = personas_path.read_text(encoding="utf-8", errors="ignore")
        # Cherche les agent_id dans AGENT_PERSONAS dict
        matches = re.findall(r'"([a-z_]+)":\s*\{[^}]*"name":\s*"([^"]+)"', source)
        for agent_id, name in matches:
            node_id = f"agent::{agent_id}"
            agent_file = f"agents/{agent_id}_agent.py"
            graph.add_node(GraphNode(
                node_id=node_id, node_type="agent",
                label=name, path=agent_file,
                metadata={"agent_id": agent_id},
            ))
            if agent_file in graph.nodes:
                graph.add_edge(agent_file, node_id, "defines")
    except Exception as e:
        logger.debug(f"Agent nodes skip: {e}")


def _add_endpoint_nodes(graph: CodeGraph) -> None:
    """Extrait les endpoints FastAPI depuis les routers."""
    routers_dir = _PROJECT_ROOT / "api" / "routers"
    if not routers_dir.exists():
        return
    for router_file in routers_dir.glob("*.py"):
        rel = str(router_file.relative_to(_PROJECT_ROOT)).replace("\\", "/")
        source = router_file.read_text(encoding="utf-8", errors="ignore")
        # @router.get("/path") ou @router.post("/path")
        matches = re.findall(r'@router\.(get|post|put|delete|patch)\("([^"]+)"', source)
        for method, path in matches:
            node_id = f"endpoint::{method.upper()}::{path}"
            graph.add_node(GraphNode(
                node_id=node_id, node_type="endpoint",
                label=f"{method.upper()} {path}", path=rel,
                metadata={"http_method": method.upper(), "path": path},
            ))
            graph.add_edge(rel, node_id, "exposes")


def _add_table_hints(graph: CodeGraph) -> None:
    """Détecte les tables Supabase via .table("name") dans le code."""
    seen_tables: set[str] = set()
    for py_file in _PROJECT_ROOT.rglob("*.py"):
        parts = py_file.relative_to(_PROJECT_ROOT).parts
        if any(p in _IGNORE_DIRS for p in parts):
            continue
        try:
            source = py_file.read_text(encoding="utf-8", errors="ignore")
            matches = re.findall(r'\.table\("([^"]+)"\)', source)
            rel = str(py_file.relative_to(_PROJECT_ROOT)).replace("\\", "/")
            for table in matches:
                table_id = f"table::{table}"
                if table_id not in graph.nodes:
                    graph.add_node(GraphNode(
                        node_id=table_id, node_type="table",
                        label=table, path=None,
                        metadata={"supabase_table": True},
                    ))
                    seen_tables.add(table)
                if rel in graph.nodes:
                    graph.add_edge(rel, table_id, "uses")
        except Exception:
            pass


# ---------------------------------------------------------------------------
# Query interface — LLM répond sur le graphe
# ---------------------------------------------------------------------------

_GRAPH_QUERY_SYSTEM = """Tu es Axel Roux, Data Analyst ALNUA.
Tu réponds à des questions sur l'architecture du codebase ALNUA en analysant
le contexte graphe fourni.
Sois précis, cite les nœuds et relations pertinents.
Réponds en JSON valide."""


def query_graph(
    question: str,
    agent_id: str = "analyst_data",
    rebuild: bool = False,
) -> dict[str, Any]:
    """
    Répond à une question sur l'architecture en langage naturel.

    Endpoint: POST /services/code-graph/query
    """
    global _GRAPH_CACHE
    if rebuild:
        _GRAPH_CACHE = None

    graph = _get_or_build_graph()

    # Contexte graphe complet en JSON compact
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
    graph = _get_or_build_graph()

    agent_node_id = f"agent::{agent_id}"
    agent_file = f"agents/{agent_id}_agent.py"

    node = graph.nodes.get(agent_node_id) or graph.nodes.get(agent_file)
    if not node:
        return {"error": f"Agent '{agent_id}' not found in graph", "agent_id": agent_id}

    # Fichier agent + ses imports
    imports = graph.neighbors(agent_file, "imports")
    defines = graph.neighbors(agent_file, "defines")

    # Endpoints qui pourraient appeler cet agent (heuristique sur le chemin)
    endpoints = [
        n.to_dict() for n in graph.find_nodes("endpoint")
        if agent_id.replace("_", "-") in n.label.lower()
        or agent_id in n.label.lower()
    ]

    # Tables utilisées par le fichier agent
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
    global _GRAPH_CACHE
    if rebuild:
        _GRAPH_CACHE = None

    graph = _get_or_build_graph()

    # Top fichiers (par nombre d'imports entrants = les plus dépendants)
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


def invalidate_cache() -> dict[str, str]:
    """Force rebuild du graphe au prochain appel."""
    global _GRAPH_CACHE
    _GRAPH_CACHE = None
    return {"status": "cache invalidated"}
