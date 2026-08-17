from __future__ import annotations

from typing import Any

from src.models.entities import (
    Benchmark,
    Limitation,
    Method,
    Paper,
    ResearchDirection,
    ResearchProblem,
    Task,
)
from src.models.relationships import RELATIONSHIP_TYPE_MAP, BaseRelationship, validate_relationship_compatibility
from src.knowledge.state import KnowledgeState


class KnowledgeStateValidationError(ValueError):
    """Raised when a knowledge state violates the dataset rules."""


class KnowledgeStateValidator:
    """Validate a knowledge state and report errors without modifying it."""

    def __init__(self, state: KnowledgeState) -> None:
        self.state = state

    def validate(self) -> list[str]:
        errors: list[str] = []
        entity_map = self._build_entity_map()

        for relationship in self.state.relationships:
            if relationship.source_id not in entity_map:
                errors.append(f"Relationship source entity missing: {relationship.source_id}")
                continue
            if relationship.target_id not in entity_map:
                errors.append(f"Relationship target entity missing: {relationship.target_id}")
                continue

            source_entity = entity_map[relationship.source_id]
            target_entity = entity_map[relationship.target_id]
            try:
                validate_relationship_compatibility(source_entity, target_entity, relationship.relationship_type)
            except ValueError as exc:
                errors.append(f"Invalid relationship {relationship.relationship_type}: {exc}")

        return errors

    def _build_entity_map(self) -> dict[str, object]:
        entity_map: dict[str, object] = {}
        for collection in (
            self.state.papers,
            self.state.research_problems,
            self.state.methods,
            self.state.tasks,
            self.state.benchmarks,
            self.state.limitations,
            self.state.research_directions,
        ):
            for entity in collection:
                if isinstance(entity, Paper):
                    entity_map[entity.paper_id] = entity
                elif isinstance(entity, ResearchProblem):
                    entity_map[entity.problem_id] = entity
                elif isinstance(entity, Method):
                    entity_map[entity.method_id] = entity
                elif isinstance(entity, Task):
                    entity_map[entity.task_id] = entity
                elif isinstance(entity, Benchmark):
                    entity_map[entity.benchmark_id] = entity
                elif isinstance(entity, Limitation):
                    entity_map[entity.limitation_id] = entity
                elif isinstance(entity, ResearchDirection):
                    entity_map[entity.direction_id] = entity
        return entity_map


def validate_knowledge_state(state: KnowledgeState) -> list[str]:
    return KnowledgeStateValidator(state).validate()
