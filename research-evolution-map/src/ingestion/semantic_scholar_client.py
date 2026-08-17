from __future__ import annotations

import logging
from typing import Any

import httpx

logger = logging.getLogger(__name__)


class SemanticScholarClient:
    """Minimal Semantic Scholar API client with retry handling."""

    def __init__(
        self,
        *,
        base_url: str = "https://api.semanticscholar.org/graph/v1/paper/search",
        timeout: float = 15.0,
        max_retries: int = 3,
    ) -> None:
        self.base_url = base_url
        self.timeout = timeout
        self.max_retries = max_retries

    def search(self, query: str, page: int = 1, page_size: int = 10) -> list[dict[str, Any]]:
        params = {
            "query": query,
            "limit": page_size,
            "offset": (page - 1) * page_size,
            "fields": "paperId,title,authors,abstract,year,venue,url,citationCount,references",
        }

        last_error: Exception | None = None
        for attempt in range(1, self.max_retries + 1):
            try:
                response = httpx.get(self.base_url, params=params, timeout=self.timeout)
                response.raise_for_status()
                payload = response.json()
                return payload.get("data", [])
            except Exception as exc:  # pragma: no cover - retry logic handled here
                last_error = exc
                logger.warning("Semantic Scholar request failed (attempt %s/%s): %s", attempt, self.max_retries, exc)
                if attempt < self.max_retries:
                    continue

        raise RuntimeError(f"Semantic Scholar search failed after {self.max_retries} attempts") from last_error
