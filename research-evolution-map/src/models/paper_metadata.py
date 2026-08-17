from __future__ import annotations

from pydantic import BaseModel, Field, HttpUrl


class PaperMetadata(BaseModel):
    """Normalized paper metadata record for ingestion."""

    paper_id: str = Field(..., min_length=1)
    title: str = Field(..., min_length=1)
    authors: list[str] = Field(default_factory=list)
    abstract: str | None = None
    year: int | None = None
    venue: str | None = None
    source: str = Field(..., min_length=1)
    url: HttpUrl | str | None = None
    citation_count: int | None = Field(default=None, ge=0)
    reference_ids: list[str] = Field(default_factory=list)
