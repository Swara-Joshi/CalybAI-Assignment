from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from src.config.settings import ResearchConfig
from src.models.paper_metadata import PaperMetadata

from .arxiv_client import ArxivClient
from .semantic_scholar_client import SemanticScholarClient

logger = logging.getLogger(__name__)


class PaperIngestor:
    """Collect and normalize research papers for the configured scope."""

    def __init__(self, *, config: ResearchConfig, project_root: str | Path | None = None) -> None:
        self.config = config
        self.project_root = Path(project_root) if project_root else Path(__file__).resolve().parents[2]
        self.raw_dir = self.project_root / "data" / "raw"
        self.processed_dir = self.project_root / "data" / "processed"
        self.raw_dir.mkdir(parents=True, exist_ok=True)
        self.processed_dir.mkdir(parents=True, exist_ok=True)
        self.arxiv_client = ArxivClient()
        self.semantic_client = SemanticScholarClient()

    def ingest_all(self) -> dict[str, int]:
        seen_ids: set[str] = set()
        records: list[PaperMetadata] = []
        duplicates_removed = 0
        missing_metadata = 0

        for query in self.config.queries:
            for source in self.config.sources:
                for page in self._iter_pages():
                    if source.lower() == "arxiv":
                        results = self.arxiv_client.search(query, page=page, page_size=10)
                    elif source.lower() == "semantic scholar":
                        results = self.semantic_client.search(query, page=page, page_size=10)
                    else:
                        continue

                    self._store_raw_response(source, query, page, results)

                    for result in results:
                        paper = self._normalize_result(source, result)
                        if paper is None:
                            continue

                        stable_id = self._stable_identifier(paper)
                        if stable_id in seen_ids:
                            duplicates_removed += 1
                            continue

                        seen_ids.add(stable_id)
                        records.append(paper)

                        if len(records) >= self.config.max_paper_count:
                            break

                    if len(records) >= self.config.max_paper_count:
                        break
                if len(records) >= self.config.max_paper_count:
                    break
            if len(records) >= self.config.max_paper_count:
                break

        normalized_records = [self._normalize_missing_fields(record) for record in records]
        missing_metadata = sum(1 for record in normalized_records if self._has_missing_required_metadata(record))
        self._store_processed_records(normalized_records)

        summary = {
            "papers_collected": len(normalized_records),
            "duplicates_removed": duplicates_removed,
            "papers_successfully_normalized": len(normalized_records),
            "papers_with_missing_metadata": missing_metadata,
        }
        logger.info("Ingestion summary: %s", summary)
        return summary

    def _iter_pages(self) -> list[int]:
        max_pages = max(1, (self.config.max_paper_count + 9) // 10)
        return list(range(1, max_pages + 1))

    def _store_raw_response(self, source: str, query: str, page: int, payload: Any) -> None:
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        file_name = f"{source.lower().replace(' ', '_')}_{query.lower().replace(' ', '_')}_page_{page}_{timestamp}.json"
        destination = self.raw_dir / file_name
        destination.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")

    def _store_processed_records(self, records: list[PaperMetadata]) -> None:
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        destination = self.processed_dir / f"normalized_papers_{timestamp}.json"
        destination.write_text(
            json.dumps([record.model_dump(mode="json") for record in records], indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

    def _normalize_result(self, source: str, result: dict[str, Any]) -> PaperMetadata | None:
        if source.lower() == "arxiv":
            paper_id = result.get("id") or ""
            title = result.get("title") or ""
            authors = result.get("authors") or []
            abstract = result.get("summary")
            published = result.get("published")
            year = self._parse_year(published)
            venue = result.get("journal_ref")
            url = self._extract_arxiv_url(result)
            citation_count = None
            reference_ids = []
        elif source.lower() == "semantic scholar":
            paper_id = result.get("paperId") or ""
            title = result.get("title") or ""
            authors = [author.get("name", "") for author in result.get("authors", []) if author.get("name")]
            abstract = result.get("abstract")
            year = result.get("year")
            venue = result.get("venue")
            url = result.get("url")
            citation_count = result.get("citationCount")
            reference_ids = [ref.get("paperId") for ref in result.get("references", []) if ref.get("paperId")]
        else:
            return None

        if not paper_id or not title:
            return None

        return PaperMetadata(
            paper_id=paper_id,
            title=title,
            authors=authors,
            abstract=abstract,
            year=year,
            venue=venue,
            source=source.lower(),
            url=url,
            citation_count=citation_count,
            reference_ids=reference_ids,
        )

    def _normalize_missing_fields(self, record: PaperMetadata) -> PaperMetadata:
        if not record.abstract:
            record.abstract = "Missing abstract"
        if not record.venue:
            record.venue = "Unknown"
        if not record.url:
            record.url = "https://example.invalid/" + record.paper_id
        return record

    def _has_missing_required_metadata(self, record: PaperMetadata) -> bool:
        return bool(
            not record.title
            or not record.authors
            or not record.abstract
            or record.year is None
            or not record.venue
            or not record.url
        )

    def _stable_identifier(self, record: PaperMetadata) -> str:
        return record.paper_id.strip().lower()

    def _parse_year(self, value: str | None) -> int | None:
        if not value:
            return None
        try:
            return datetime.fromisoformat(value[:10]).year
        except ValueError:
            return None

    def _extract_arxiv_url(self, result: dict[str, Any]) -> str | None:
        links = result.get("links") or []
        if not links:
            return None
        hrefs = [link.get("href") for link in links if isinstance(link, dict) and link.get("href")]
        return hrefs[0] if hrefs else None
