from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, field_validator

from src.models.entities import (
    Benchmark,
    Limitation,
    Method,
    Paper,
    ResearchDirection,
    ResearchProblem,
    Task,
)


class BaseRelationship(BaseModel):
    """Base relationship representation."""

    source_id: str = Field(..., min_length=1)
    target_id: str = Field(..., min_length=1)
    relationship_type: str = Field(..., min_length=1)


class SemanticRelationship(BaseRelationship):
    """Relationship with evidence and confidence metadata."""

    evidence: str = Field(..., min_length=1)
    source_paper_id: str = Field(..., min_length=1)
    confidence: float = Field(..., ge=0.0, le=1.0)


class PaperAddressesProblem(SemanticRelationship):
    source_id: str
    target_id: str
    relationship_type: Literal["addresses"] = "addresses"


class PaperProposesMethod(SemanticRelationship):
    source_id: str
    target_id: str
    relationship_type: Literal["proposes"] = "proposes"


class MethodTargetsTask(SemanticRelationship):
    source_id: str
    target_id: str
    relationship_type: Literal["targets"] = "targets"


class PaperEvaluatesOnBenchmark(SemanticRelationship):
    source_id: str
    target_id: str
    relationship_type: Literal["evaluates_on"] = "evaluates_on"


class PaperIdentifiesLimitation(SemanticRelationship):
    source_id: str
    target_id: str
    relationship_type: Literal["identifies"] = "identifies"


class PaperExtendsPaper(SemanticRelationship):
    source_id: str
    target_id: str
    relationship_type: Literal["extends"] = "extends"


class PaperChallengesPaper(SemanticRelationship):
    source_id: str
    target_id: str
    relationship_type: Literal["challenges"] = "challenges"


class MethodImprovesUponMethod(SemanticRelationship):
    source_id: str
    target_id: str
    relationship_type: Literal["improves_upon"] = "improves_upon"


class LimitationMotivatesDirection(SemanticRelationship):
    source_id: str
    target_id: str
    relationship_type: Literal["motivates"] = "motivates"


class ResearchDirectionExploredByPaper(SemanticRelationship):
    source_id: str
    target_id: str
    relationship_type: Literal["explored_by"] = "explored_by"


class PaperCitesPaper(SemanticRelationship):
    source_id: str
    target_id: str
    relationship_type: Literal["cites"] = "cites"


RELATIONSHIP_TYPE_MAP = {
    "addresses": (Paper, ResearchProblem),
    "proposes": (Paper, Method),
    "targets": (Method, Task),
    "evaluates_on": (Paper, Benchmark),
    "identifies": (Paper, Limitation),
    "extends": (Paper, Paper),
    "challenges": (Paper, Paper),
    "improves_upon": (Method, Method),
    "motivates": (Limitation, ResearchDirection),
    "explored_by": (ResearchDirection, Paper),
    "cites": (Paper, Paper),
}


def validate_relationship_compatibility(source_entity: object, target_entity: object, relationship_type: str) -> None:
    if relationship_type not in RELATIONSHIP_TYPE_MAP:
        raise ValueError(f"Unsupported relationship_type: {relationship_type}")

    expected_types = RELATIONSHIP_TYPE_MAP[relationship_type]
    if not isinstance(source_entity, expected_types[0]):
        raise ValueError(
            f"Relationship '{relationship_type}' requires source entity type {expected_types[0].__name__}"
        )
    if not isinstance(target_entity, expected_types[1]):
        raise ValueError(
            f"Relationship '{relationship_type}' requires target entity type {expected_types[1].__name__}"
        )
