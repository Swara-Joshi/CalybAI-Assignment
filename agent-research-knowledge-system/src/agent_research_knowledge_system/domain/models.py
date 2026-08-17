from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Literal

from pydantic import BaseModel, Field, HttpUrl


class ResearchPaper(BaseModel):
    """Structured metadata describing a single research paper."""

    paper_id: str = Field(..., min_length=1)
    title: str = Field(..., min_length=1)
    authors: list[str] = Field(default_factory=list)
    venue: str | None = None
    year: int | None = None
    doi: str | None = None
    url: HttpUrl | None = None
    abstract: str | None = None
    source_type: Literal["arxiv", "pdf", "manual", "other"] = "manual"
    added_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    tags: list[str] = Field(default_factory=list)
    raw_metadata: dict[str, Any] = Field(default_factory=dict)


class ResearchClaim(BaseModel):
    """General representation of a claim or proposition extracted from a paper."""

    claim_id: str = Field(..., min_length=1)
    paper_id: str = Field(..., min_length=1)
    text: str = Field(..., min_length=1)
    category: str | None = None
    confidence: float | None = Field(default=None, ge=0.0, le=1.0)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: dict[str, Any] = Field(default_factory=dict)


class KnowledgeSnapshot(BaseModel):
    """Snapshot of the system's current knowledge state."""

    snapshot_id: str = Field(..., min_length=1)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    source_count: int = 0
    claim_count: int = 0
    summary: str = ""
    metadata: dict[str, Any] = Field(default_factory=dict)
