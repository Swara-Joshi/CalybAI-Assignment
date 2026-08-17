from __future__ import annotations

from pathlib import Path

from src.config.settings import ResearchConfig
from src.ingestion.arxiv_client import ArxivClient
from src.ingestion.paper_ingestor import PaperIngestor
from src.ingestion.semantic_scholar_client import SemanticScholarClient


def test_ingestion_pipeline_deduplicates_and_normalizes(tmp_path, monkeypatch) -> None:
    config = ResearchConfig(
        topic="Evolution of LLM Agent Research",
        subtopics=["planning"],
        target_paper_count=5,
        min_paper_count=2,
        max_paper_count=10,
        sources=["arXiv", "Semantic Scholar"],
        queries=["LLM agent planning research"],
        date_range={"start": "2022-01-01", "end": "2025-12-31"},
    )

    def fake_arxiv_search(self, query: str, page: int = 1, page_size: int = 10):
        return [
            {
                "id": "2401.00001v1",
                "title": "Planning in LLM Agents",
                "authors": ["Alice Smith", "Bob Jones"],
                "summary": "A planning paper.",
                "published": "2024-01-10",
                "journal_ref": "NeurIPS",
                "links": [{"href": "https://arxiv.org/abs/2401.00001"}],
            },
            {
                "id": "2401.00001v1",
                "title": "Planning in LLM Agents",
                "authors": ["Alice Smith", "Bob Jones"],
                "summary": "A planning paper.",
                "published": "2024-01-10",
                "journal_ref": "NeurIPS",
                "links": [{"href": "https://arxiv.org/abs/2401.00001"}],
            },
        ]

    def fake_semantic_search(self, query: str, page: int = 1, page_size: int = 10):
        return [
            {
                "paperId": "ss-123",
                "title": "Tool Use in Agentic Models",
                "authors": [{"name": "Carol White"}],
                "abstract": "A tool use paper.",
                "year": 2024,
                "venue": "ICML",
                "url": "https://www.semanticscholar.org/paper/ss-123",
                "citationCount": 15,
                "references": [{"paperId": "ref-1"}],
            }
        ]

    monkeypatch.setattr(ArxivClient, "search", fake_arxiv_search)
    monkeypatch.setattr(SemanticScholarClient, "search", fake_semantic_search)

    ingestor = PaperIngestor(config=config, project_root=tmp_path)
    result = ingestor.ingest_all()

    assert result["papers_collected"] == 2
    assert result["duplicates_removed"] == 1
    assert result["papers_successfully_normalized"] == 2
    assert result["papers_with_missing_metadata"] == 0

    raw_dir = Path(tmp_path) / "data" / "raw"
    processed_dir = Path(tmp_path) / "data" / "processed"
    assert raw_dir.exists()
    assert processed_dir.exists()
    assert any(raw_dir.iterdir())
    assert any(processed_dir.iterdir())


def test_paper_metadata_requires_minimal_values() -> None:
    from src.models.paper_metadata import PaperMetadata

    metadata = PaperMetadata(
        paper_id="arxiv:2401.00001",
        title="Sample Paper",
        authors=["Alice"],
        abstract="A short abstract.",
        year=2024,
        venue="ICML",
        source="arxiv",
        url="https://example.com/paper",
        citation_count=10,
        reference_ids=["ref-1"],
    )

    assert metadata.paper_id == "arxiv:2401.00001"
    assert metadata.reference_ids == ["ref-1"]
