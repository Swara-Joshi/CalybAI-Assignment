from __future__ import annotations

import json
import logging
from pathlib import Path

from src.knowledge.citations import build_citation_graph, load_papers_from_processed

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
logger = logging.getLogger(__name__)


def main() -> None:
    project_root = Path(__file__).resolve().parents[1]
    processed_dir = project_root / "data" / "processed"
    papers_path = sorted(processed_dir.glob("*.json"))[-1]
    papers = load_papers_from_processed(papers_path)
    graph = build_citation_graph(papers)
    stats = graph.statistics()

    print(json.dumps({
        "number_of_papers": stats["number_of_papers"],
        "number_of_citation_relationships": stats["number_of_citation_relationships"],
        "most_cited_papers": stats["most_cited_papers"],
        "papers_with_no_internal_citations": stats["papers_with_no_internal_citations"],
        "papers_with_no_outgoing_citations": stats["papers_with_no_outgoing_citations"],
    }, indent=2))

    logger.info("number of papers: %s", stats["number_of_papers"])
    logger.info("number of citation relationships: %s", stats["number_of_citation_relationships"])
    logger.info("most cited papers: %s", stats["most_cited_papers"])
    logger.info("papers with no internal citations: %s", stats["papers_with_no_internal_citations"])
    logger.info("papers with no outgoing citations: %s", stats["papers_with_no_outgoing_citations"])


if __name__ == "__main__":
    main()
