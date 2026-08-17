from __future__ import annotations

from collections import defaultdict, deque
from typing import Any

from src.knowledge.state import KnowledgeState


class TraversalResult:
    """Explicit path traversal result over the knowledge state."""

    def __init__(self, knowledge_state: KnowledgeState, start_nodes: list[str], max_depth: int = 3) -> None:
        self.knowledge_state = knowledge_state
        self.start_nodes = start_nodes
        self.max_depth = max_depth
        self.paths = self._traverse()

    def _traverse(self) -> list[list[str]]:
        adjacency: dict[str, list[str]] = defaultdict(list)
        for rel in self.knowledge_state.relationships:
            adjacency[rel.source_id].append(rel.target_id)

        results: list[list[str]] = []
        for start in self.start_nodes:
            queue: deque[tuple[str, list[str]]] = deque([(start, [start])])
            seen: set[str] = {start}
            while queue:
                current, path = queue.popleft()
                if len(path) - 1 >= self.max_depth:
                    continue
                for neighbor in adjacency.get(current, []):
                    if neighbor in seen:
                        continue
                    seen.add(neighbor)
                    new_path = path + [neighbor]
                    results.append(new_path)
                    queue.append((neighbor, new_path))
        return results
