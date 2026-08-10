"""Build the ALNUA codebase knowledge graph from Python AST + heuristics."""

from __future__ import annotations

import ast
import logging
import re
import time
from pathlib import Path

from services.code_graph_models import CodeGraph, GraphNode

logger = logging.getLogger(__name__)

_PROJECT_ROOT = Path(__file__).parent.parent

_IGNORE_DIRS = {
    "__pycache__", ".git", "node_modules", ".venv", "venv",
    "build", "dist", ".next", ".claude", "data",
}
_IGNORE_FILES = {"__init__.py"}


def build_graph() -> CodeGraph:
    """Construit le graphe en parsant les fichiers Python du projet."""
    graph = CodeGraph()
    logger.info("Building code graph...")
    start = time.time()

    python_files = _collect_python_files()

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

    _add_agent_nodes(graph)
    _add_endpoint_nodes(graph)
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
        if isinstance(node, ast.ClassDef):
            class_id = f"{file_id}::{node.name}"
            graph.add_node(GraphNode(
                node_id=class_id, node_type="class",
                label=node.name, path=rel_path,
                metadata={"lineno": node.lineno},
            ))
            graph.add_edge(file_id, class_id, "defines")

            for item in node.body:
                if isinstance(item, ast.FunctionDef):
                    method_id = f"{class_id}.{item.name}"
                    graph.add_node(GraphNode(
                        node_id=method_id, node_type="function",
                        label=f"{node.name}.{item.name}", path=rel_path,
                        metadata={"lineno": item.lineno},
                    ))
                    graph.add_edge(class_id, method_id, "defines")

            for base in node.bases:
                if isinstance(base, ast.Name):
                    graph.add_edge(class_id, base.id, "inherits")

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

        elif isinstance(node, ast.Import):
            for alias in node.names:
                _add_import_edge(graph, file_id, alias.name)

        elif isinstance(node, ast.ImportFrom):
            if node.module:
                _add_import_edge(graph, file_id, node.module)


def _add_import_edge(graph: CodeGraph, file_id: str, module: str) -> None:
    """Convertit un import en arête s'il pointe vers un fichier du projet."""
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
