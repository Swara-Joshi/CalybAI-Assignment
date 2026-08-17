from __future__ import annotations

from pydantic import BaseModel, Field, field_validator


class Paper(BaseModel):
    """Research paper entity."""

    paper_id: str = Field(..., min_length=1)
    title: str = Field(..., min_length=1)
    authors: list[str] = Field(default_factory=list)
    year: int | None = None
    abstract: str | None = None
    venue: str | None = None
    source: str | None = None
    url: str | None = None


class ResearchProblem(BaseModel):
    """Research problem entity."""

    problem_id: str = Field(..., min_length=1)
    name: str = Field(..., min_length=1)
    description: str | None = None


class Method(BaseModel):
    """Method entity."""

    method_id: str = Field(..., min_length=1)
    name: str = Field(..., min_length=1)
    description: str | None = None


class Task(BaseModel):
    """Task entity."""

    task_id: str = Field(..., min_length=1)
    name: str = Field(..., min_length=1)
    description: str | None = None


class Benchmark(BaseModel):
    """Benchmark entity."""

    benchmark_id: str = Field(..., min_length=1)
    name: str = Field(..., min_length=1)
    description: str | None = None


class Limitation(BaseModel):
    """Limitation entity."""

    limitation_id: str = Field(..., min_length=1)
    name: str = Field(..., min_length=1)
    description: str | None = None


class ResearchDirection(BaseModel):
    """Research direction entity."""

    direction_id: str = Field(..., min_length=1)
    name: str = Field(..., min_length=1)
    description: str | None = None


Entity = Paper | ResearchProblem | Method | Task | Benchmark | Limitation | ResearchDirection
