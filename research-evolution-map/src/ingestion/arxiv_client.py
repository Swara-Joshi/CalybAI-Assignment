from __future__ import annotations

import logging
from datetime import datetime
from typing import Any

import httpx

logger = logging.getLogger(__name__)


class ArxivClient:
    """Minimal arXiv API client with retries and pagination support."""

    def __init__(
        self,
        *,
        base_url: str = "http://export.arxiv.org/api/query",
        timeout: float = 15.0,
        max_retries: int = 3,
    ) -> None:
        self.base_url = base_url
        self.timeout = timeout
        self.max_retries = max_retries

    def search(self, query: str, page: int = 1, page_size: int = 10) -> list[dict[str, Any]]:
        """Search arXiv and return raw result objects.

        This intentionally keeps the response structure simple and stable for the
        current project stage.
        """
        params = {
            "search_query": f"all:{query}",
            "start": str((page - 1) * page_size + 1),
            "max_results": str(page_size),
        }

        last_error: Exception | None = None
        for attempt in range(1, self.max_retries + 1):
            try:
                response = httpx.get(self.base_url, params=params, timeout=self.timeout)
                response.raise_for_status()
                return self._parse_response(response.text)
            except Exception as exc:  # pragma: no cover - retry logic handled here
                last_error = exc
                logger.warning("arXiv request failed (attempt %s/%s): %s", attempt, self.max_retries, exc)
                if attempt < self.max_retries:
                    continue

        raise RuntimeError(f"arXiv search failed after {self.max_retries} attempts") from last_error

    def _parse_response(self, payload: str) -> list[dict[str, Any]]:
        """Parse simple XML from arXiv into a list of dictionaries."""
        items: list[dict[str, Any]] = []
        if "<entry>" not in payload:
            return items

        chunks = payload.split("<entry>")
        for chunk in chunks[1:]:
            entry = {"id": "", "title": "", "authors": [], "summary": "", "published": "", "journal_ref": "", "links": []}
            if "<id>" in chunk:
                entry["id"] = chunk.split("<id>", 1)[1].split("</id>", 1)[0].strip()
            if "<title>" in chunk:
                entry["title"] = chunk.split("<title>", 1)[1].split("</title>", 1)[0].strip()
            if "<name>" in chunk:
                names = []
                for name in chunk.split("<name>")[1:]:
                    names.append(name.split("</name>", 1)[0].strip())
                entry["authors"] = names
            if "<summary>" in chunk:
                entry["summary"] = chunk.split("<summary>", 1)[1].split("</summary>", 1)[0].strip()
            if "<published>" in chunk:
                entry["published"] = chunk.split("<published>", 1)[1].split("</published>", 1)[0].strip()
            if "<journal_ref>" in chunk:
                entry["journal_ref"] = chunk.split("<journal_ref>", 1)[1].split("</journal_ref>", 1)[0].strip()
            if "<link" in chunk:
                links = []
                for link in chunk.split('<link')[1:]:
                    href = link.split('href="', 1)[1].split('"', 1)[0] if 'href="' in link else ""
                    if href:
                        links.append({"href": href})
                entry["links"] = links
            items.append(entry)
        return items
