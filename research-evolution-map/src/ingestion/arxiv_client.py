from __future__ import annotations

import logging
import xml.etree.ElementTree as ET
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
            "start": str((page - 1) * page_size),
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
        namespace = "{http://www.w3.org/2005/Atom}"
        root = ET.fromstring(payload)
        items: list[dict[str, Any]] = []
        for node in root.findall(f"{namespace}entry"):
            def text(name: str) -> str:
                value = node.findtext(f"{namespace}{name}")
                return value.strip() if value else ""

            items.append(
                {
                    "id": text("id"),
                    "title": text("title"),
                    "authors": [
                        name.text.strip()
                        for name in node.findall(f"{namespace}author/{namespace}name")
                        if name.text and name.text.strip()
                    ],
                    "summary": text("summary"),
                    "published": text("published"),
                    "journal_ref": text("journal_ref"),
                    "links": [
                        {"href": link.attrib["href"]}
                        for link in node.findall(f"{namespace}link")
                        if link.attrib.get("href")
                    ],
                }
            )
        return items
