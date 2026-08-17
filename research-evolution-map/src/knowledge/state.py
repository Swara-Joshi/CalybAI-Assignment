from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field

from src.models.entities import (
    Benchmark,
    Limitation,
    Method,
    Paper,
    ResearchDirection,
    ResearchProblem,
    Task,
)
from src.models.relationships import BaseRelationship


class StateMetadata(BaseModel):
    """Metadata for a serialized knowledge state."""

    schema_version: str = Field(default="1.0")
    dataset_name: str = Field(default="research-evolution-map")
    paper_count: int = Field(default=0)
    generated_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    source_information: dict[str, Any] = Field(default_factory=dict)


class KnowledgeState(BaseModel):
    """Serializable knowledge state for a dataset snapshot."""

    metadata: StateMetadata = Field(default_factory=StateMetadata)
    papers: list[Paper] = Field(default_factory=list)
    research_problems: list[ResearchProblem] = Field(default_factory=list)
    methods: list[Method] = Field(default_factory=list)
    tasks: list[Task] = Field(default_factory=list)
    benchmarks: list[Benchmark] = Field(default_factory=list)
    limitations: list[Limitation] = Field(default_factory=list)
    research_directions: list[ResearchDirection] = Field(default_factory=list)
    relationships: list[BaseRelationship] = Field(default_factory=list)

    def add_entity(self, entity: object) -> None:
        if isinstance(entity, Paper):
            self.papers.append(entity)
        elif isinstance(entity, ResearchProblem):
            self.research_problems.append(entity)
        elif isinstance(entity, Method):
            self.methods.append(entity)
        elif isinstance(entity, Task):
            self.tasks.append(entity)
        elif isinstance(entity, Benchmark):
            self.benchmarks.append(entity)
        elif isinstance(entity, Limitation):
            self.limitations.append(entity)
        elif isinstance(entity, ResearchDirection):
            self.research_directions.append(entity)
        else:
            raise TypeError(f"Unsupported entity type: {type(entity).__name__}")

        self.metadata.paper_count = len(self.papers)

    def add_relationship(self, relationship: BaseRelationship) -> None:
        self.relationships.append(relationship)

    def _lookup_entity(self, entity_id: str) -> object | None:
        for collection in (
            self.papers,
            self.research_problems,
            self.methods,
            self.tasks,
            self.benchmarks,
            self.limitations,
            self.research_directions,
        ):
            for entity in collection:
                if isinstance(entity, Paper) and entity.paper_id == entity_id:
                    return entity
                if isinstance(entity, ResearchProblem) and entity.problem_id == entity_id:
                    return entity
                if isinstance(entity, Method) and entity.method_id == entity_id:
                    return entity
                if isinstance(entity, Task) and entity.task_id == entity_id:
                    return entity
                if isinstance(entity, Benchmark) and entity.benchmark_id == entity_id:
                    return entity
                if isinstance(entity, Limitation) and entity.limitation_id == entity_id:
                    return entity
                if isinstance(entity, ResearchDirection) and entity.direction_id == entity_id:
                    return entity
        return None

    def statistics(self) -> dict[str, int]:
        return {
            "papers": len(self.papers),
            "research_problems": len(self.research_problems),
            "methods": len(self.methods),
            "tasks": len(self.tasks),
            "benchmarks": len(self.benchmarks),
            "limitations": len(self.limitations),
            "research_directions": len(self.research_directions),
            "relationships": len(self.relationships),
        }
