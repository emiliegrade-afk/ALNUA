"""
Arbor-inspired hypothesis tree for ALNUA R&D.

Coordinator (this module) owns persistent trees; executors run isolated
investigations and return evidence. Insights backpropagate to ancestors.
"""

from __future__ import annotations

import threading

from config.paths import data_dir

TREES_DIR = data_dir("rnd_trees")
WATCH_TOPICS_FILE = data_dir("rnd_watch_topics.json")

from services.rnd_hypothesis_tree_helpers import (  # noqa: E402
    NodeStatus,
    TreeStatus,
    _load_tree,
    _match_watch_topics,
    _save_tree,
)
from services.rnd_hypothesis_tree_llm import _ideate_branches  # noqa: E402
from services.rnd_hypothesis_tree_mutations import (  # noqa: E402
    expand_node,
    promote_node_to_dossier,
    reparent_node,
    run_node,
    set_node_status,
    start_investigation,
)
from services.rnd_hypothesis_tree_query import (  # noqa: E402
    build_tree_graph,
    get_tree,
    get_watch_topics,
    list_trees,
)

__all__ = [
    "NodeStatus",
    "TreeStatus",
    "TREES_DIR",
    "WATCH_TOPICS_FILE",
    "threading",
    "list_trees",
    "get_tree",
    "get_watch_topics",
    "build_tree_graph",
    "start_investigation",
    "expand_node",
    "run_node",
    "set_node_status",
    "reparent_node",
    "promote_node_to_dossier",
    "_match_watch_topics",
    "_ideate_branches",
    "_load_tree",
    "_save_tree",
]
