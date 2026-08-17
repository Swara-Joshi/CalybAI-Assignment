from src.knowledge.citations import CitationGraph, CitationRelationship, build_citation_graph
from src.models.paper_metadata import PaperMetadata


def test_citation_graph_builds_only_internal_edges() -> None:
    papers = [
        PaperMetadata(
            paper_id="p1",
            title="Paper One",
            authors=["A"],
            abstract="Alpha",
            year=2023,
            venue="Venue A",
            source="arxiv",
            url="https://example.com/p1",
            citation_count=5,
            reference_ids=["p2", "external-1"],
        ),
        PaperMetadata(
            paper_id="p2",
            title="Paper Two",
            authors=["B"],
            abstract="Beta",
            year=2024,
            venue="Venue B",
            source="semantic scholar",
            url="https://example.com/p2",
            citation_count=2,
            reference_ids=["p3"],
        ),
        PaperMetadata(
            paper_id="p3",
            title="Paper Three",
            authors=["C"],
            abstract="Gamma",
            year=2025,
            venue="Venue C",
            source="arxiv",
            url="https://example.com/p3",
            citation_count=1,
            reference_ids=[],
        ),
    ]

    graph = build_citation_graph(papers)

    assert len(graph.relationships) == 2
    assert graph.relationships[0].relationship_type == "cites"
    assert { (rel.source_paper_id, rel.target_paper_id) for rel in graph.relationships } == {
        ("p1", "p2"),
        ("p2", "p3"),
    }

    stats = graph.statistics()
    assert stats["number_of_papers"] == 3
    assert stats["number_of_citation_relationships"] == 2
    assert stats["most_cited_papers"][0]["paper_id"] == "p2"
    assert "p1" in stats["papers_with_no_internal_citations"]
    assert "p3" in stats["papers_with_no_outgoing_citations"]


def test_citation_relationship_validation() -> None:
    rel = CitationRelationship(
        source_paper_id="p1",
        target_paper_id="p2",
        relationship_type="cites",
        evidence="present in reference_ids",
    )
    assert rel.relationship_type == "cites"

    try:
        CitationRelationship(
            source_paper_id="p1",
            target_paper_id="p2",
            relationship_type="mentions",
            evidence="should fail",
        )
        assert False, "Expected ValidationError"
    except ValueError:
        pass


def test_graph_deduplicates_and_validates_internal_membership() -> None:
    papers = [
        PaperMetadata(
            paper_id="a",
            title="A",
            authors=["A1"],
            abstract="A abstract",
            year=2024,
            venue="V",
            source="arxiv",
            url="https://example.com/a",
            citation_count=1,
            reference_ids=["b", "b"],
        ),
        PaperMetadata(
            paper_id="b",
            title="B",
            authors=["B1"],
            abstract="B abstract",
            year=2024,
            venue="V",
            source="arxiv",
            url="https://example.com/b",
            citation_count=2,
            reference_ids=[],
        ),
    ]

    graph = CitationGraph(papers)
    assert len(graph.relationships) == 1

    graph.add_relationship("a", "b", evidence="internal cite")
    assert len(graph.relationships) == 1

    try:
        graph.add_relationship("a", "missing", evidence="external")
        assert False, "Expected ValueError"
    except ValueError:
        pass


def test_adding_a_paper_builds_new_internal_reference_relationships() -> None:
    first = PaperMetadata(paper_id="p1", title="First", authors=["A"], source="arxiv", reference_ids=[])
    graph = CitationGraph([first])

    second = PaperMetadata(paper_id="p2", title="Second", authors=["B"], source="arxiv", reference_ids=["p1"])
    graph.add_paper(second)

    assert [(rel.source_paper_id, rel.target_paper_id) for rel in graph.relationships] == [("p2", "p1")]
