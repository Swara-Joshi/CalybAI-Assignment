from __future__ import annotations

import logging
from pathlib import Path

from src.config.settings import ResearchConfig
from src.ingestion.paper_ingestor import PaperIngestor

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
logger = logging.getLogger(__name__)


def main() -> None:
    project_root = Path(__file__).resolve().parents[1]
    config = ResearchConfig()
    ingestor = PaperIngestor(config=config, project_root=project_root)
    summary = ingestor.ingest_all()

    logger.info("number of papers collected: %s", summary["papers_collected"])
    logger.info("number of duplicates removed: %s", summary["duplicates_removed"])
    logger.info("number of papers successfully normalized: %s", summary["papers_successfully_normalized"])
    logger.info("number of papers with missing metadata: %s", summary["papers_with_missing_metadata"])


if __name__ == "__main__":
    main()
