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


def test_arxiv_client_parses_namespaced_xml_and_uses_zero_based_pagination(monkeypatch) -> None:
    captured: dict[str, object] = {}

    class FakeResponse:
        text = """<?xml version='1.0'?>
        <feed xmlns='http://www.w3.org/2005/Atom'>
          <entry>
            <id>http://arxiv.org/abs/2401.00001</id>
            <title>  A &amp; B  </title>
            <author><name>Alice</name></author>
            <summary>Summary</summary>
            <published>2024-01-10T00:00:00Z</published>
            <link rel='alternate' href='https://arxiv.org/abs/2401.00001'/>
            <link title='pdf' href='https://arxiv.org/pdf/2401.00001'/>
          </entry>
        </feed>"""

        def raise_for_status(self) -> None:
            return None

    def fake_get(url, *, params, timeout):
        captured.update(params)
        return FakeResponse()

    monkeypatch.setattr("src.ingestion.arxiv_client.httpx.get", fake_get)
    result = ArxivClient(max_retries=1).search("agents", page=2, page_size=10)

    assert captured["start"] == "10"
    assert result[0]["title"] == "A & B"
    assert result[0]["authors"] == ["Alice"]
    assert result[0]["links"] == [
        {"href": "https://arxiv.org/abs/2401.00001"},
        {"href": "https://arxiv.org/pdf/2401.00001"},
    ]


def test_semantic_scholar_client_uses_json_payload_without_network(monkeypatch) -> None:
    captured: dict[str, object] = {}

    class FakeResponse:
        def raise_for_status(self) -> None:
            return None

        def json(self):
            return {"data": [{"paperId": "p1", "title": "Paper"}]}

    def fake_get(url, *, params, timeout):
        captured.update(params)
        return FakeResponse()

    monkeypatch.setattr("src.ingestion.semantic_scholar_client.httpx.get", fake_get)
    result = SemanticScholarClient(max_retries=1).search("agents", page=2, page_size=5)

    assert captured["offset"] == 5
    assert result == [{"paperId": "p1", "title": "Paper"}]


def test_missing_metadata_detects_blank_author_and_normalization_does_not_mutate() -> None:
    from src.models.paper_metadata import PaperMetadata

    config = ResearchConfig(
        topic="Agents", subtopics=["planning"], target_paper_count=1, min_paper_count=1,
        max_paper_count=1, sources=["arXiv"], queries=["agents"],
        date_range={"start": "2022-01-01", "end": "2025-12-31"},
    )
    ingestor = PaperIngestor(config=config, project_root=Path.cwd())
    original = PaperMetadata(paper_id="p1", title="Paper", authors=["   "], year=2024, source="arxiv")

    normalized = ingestor._normalize_missing_fields(original)

    assert normalized is not original
    assert original.abstract is None
    assert ingestor._has_missing_required_metadata(normalized)
