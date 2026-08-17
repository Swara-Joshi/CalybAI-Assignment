from __future__ import annotations

from collections import Counter
from pathlib import Path
import json
from typing import Any

from pydantic import BaseModel, Field, field_validator

from src.models.paper_metadata import PaperMetadata


class CitationRelationship(BaseModel):
    """Explicit citation relationship between papers in the selected dataset."""

    source_paper_id: str = Field(..., min_length=1)
    target_paper_id: str = Field(..., min_length=1)
    relationship_type: str = Field(default="cites")
    evidence: str | None = None

    @field_validator("relationship_type")
    @classmethod
    def validate_relationship_type(cls, value: str) -> str:
        if value != "cites":
            raise ValueError("relationship_type must be 'cites'")
        return value


class CitationGraph:
    """Simple in-memory citation graph for internal dataset references only."""

    def __init__(self, papers: list[PaperMetadata] | None = None) -> None:
        self.papers = papers or []
        self.paper_index = {paper.paper_id: paper for paper in self.papers}
        self.relationships: list[CitationRelationship] = []
        self._build()

    def _build(self) -> None:
        seen: set[tuple[str, str]] = set()
        for paper in self.papers:
            for ref in paper.reference_ids:
                if ref not in self.paper_index:
                    continue
                if paper.paper_id == ref:
                    continue
                edge = (paper.paper_id, ref)
                if edge in seen:
                    continue
                seen.add(edge)
                self.relationships.append(
                    CitationRelationship(
                        source_paper_id=paper.paper_id,
                        target_paper_id=ref,
                        relationship_type="cites",
                        evidence=f"reference_ids includes {ref}",
                    )
                )

    def add_paper(self, paper: PaperMetadata) -> None:
        if paper.paper_id in self.paper_index:
            return
        self.paper_index[paper.paper_id] = paper
        self.papers.append(paper)
        self.relationships = []
        self._build()

    def add_relationship(self, source_paper_id: str, target_paper_id: str, evidence: str | None = None) -> CitationRelationship:
        if source_paper_id not in self.paper_index:
            raise ValueError(f"source paper not found in dataset: {source_paper_id}")
        if target_paper_id not in self.paper_index:
            raise ValueError(f"target paper not found in dataset: {target_paper_id}")

        if source_paper_id == target_paper_id:
            raise ValueError("self-citation is not allowed")

        relationship = CitationRelationship(
            source_paper_id=source_paper_id,
            target_paper_id=target_paper_id,
            relationship_type="cites",
            evidence=evidence or "manual citation relationship",
        )

        if not any(
            rel.source_paper_id == relationship.source_paper_id and rel.target_paper_id == relationship.target_paper_id
            for rel in self.relationships
        ):
            self.relationships.append(relationship)
        return relationship

    def statistics(self) -> dict[str, Any]:
        incoming = Counter(rel.target_paper_id for rel in self.relationships)
        outgoing = Counter(rel.source_paper_id for rel in self.relationships)

        papers_with_no_internal_citations = sorted(
            paper.paper_id for paper in self.papers if incoming.get(paper.paper_id, 0) == 0
        )
        papers_with_no_outgoing_citations = sorted(
            paper.paper_id for paper in self.papers if outgoing.get(paper.paper_id, 0) == 0
        )
        most_cited = [
            {"paper_id": paper_id, "citation_count": count}
            for paper_id, count in incoming.most_common()
        ]

        return {
            "number_of_papers": len(self.papers),
            "number_of_citation_relationships": len(self.relationships),
            "most_cited_papers": most_cited,
            "papers_with_no_internal_citations": papers_with_no_internal_citations,
            "papers_with_no_outgoing_citations": papers_with_no_outgoing_citations,
        }


def build_citation_graph(papers: list[PaperMetadata]) -> CitationGraph:
    return CitationGraph(papers=papers)


def load_papers_from_processed(path: str | Path) -> list[PaperMetadata]:
    file_path = Path(path)
    raw = json.loads(file_path.read_text(encoding="utf-8"))
    return [PaperMetadata(**entry) for entry in raw]
