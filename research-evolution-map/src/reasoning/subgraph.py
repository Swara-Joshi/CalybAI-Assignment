from __future__ import annotations

from collections import defaultdict
from typing import Any

from src.knowledge.state import KnowledgeState


class Subgraph:
    """Explicitly scoped subset of the knowledge state for a proposal."""

    def __init__(self, knowledge_state: KnowledgeState, concept_matches: dict[str, list[str]]) -> None:
        self.knowledge_state = knowledge_state
        self.concept_matches = concept_matches
        self.nodes = self._build_nodes()
        self.edges = self._build_edges()

    def _build_nodes(self) -> set[str]:
        nodes: set[str] = set()
        for concept, matches in self.concept_matches.items():
            nodes.update(matches)
        return nodes

    def _build_edges(self) -> list[tuple[str, str, str]]:
        edges: list[tuple[str, str, str]] = []
        for relationship in self.knowledge_state.relationships:
            if relationship.source_id in self.nodes or relationship.target_id in self.nodes:
                edges.append((relationship.source_id, relationship.target_id, relationship.relationship_type))
        return edges

    def summary(self) -> dict[str, Any]:
        return {
            "nodes": sorted(self.nodes),
            "edges": [
                {"source_id": source, "target_id": target, "relationship_type": rel_type}
                for source, target, rel_type in self.edges
            ],
        }
