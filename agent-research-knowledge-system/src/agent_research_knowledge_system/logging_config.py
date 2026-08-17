from __future__ import annotations

import logging
from typing import Optional


def configure_logging(log_level: str = "INFO") -> logging.Logger:
    """Configure the application logger.

    This is intentionally simple and production-friendly without introducing complex
    logging infrastructure before the core research workflow is implemented.
    """
    logging.basicConfig(
        level=getattr(logging, log_level.upper(), logging.INFO),
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    return logging.getLogger("agent_research_knowledge_system")
