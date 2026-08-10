"""Dataclasses for the ALNUA codebase knowledge graph."""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any


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
