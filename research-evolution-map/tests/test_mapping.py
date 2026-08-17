from src.knowledge.mapping import (
    deterministic_metadata_mapping,
    map_paper_to_benchmarks,
    map_paper_to_directions,
    map_paper_to_limitations,
    map_paper_to_methods,
    map_paper_to_paper_relationships,
    map_paper_to_problems,
    map_paper_to_relationships,
    map_paper_to_tasks,
)
from src.models.entities import Paper


def test_deterministic_metadata_mapping() -> None:
    paper = Paper(
        paper_id="p1",
        title="Alpha",
        authors=["Alice", "Bob"],
        year=2024,
        abstract="Short summary",
        venue="ICML",
        source="arxiv",
        url="https://example.com/p1",
    )

    mapped = deterministic_metadata_mapping(paper)
    assert mapped["paper_id"] == "p1"
    assert mapped["title"] == "Alpha"
    assert mapped["authors"] == ["Alice", "Bob"]


def test_explicit_mapping_functions_create_structured_outputs() -> None:
    paper = Paper(
        paper_id="p1",
        title="Paper One",
        authors=["Alice"],
        year=2024,
        abstract="A planning paper.",
        venue="ICML",
        source="arxiv",
        url="https://example.com/p1",
    )

    problems = map_paper_to_problems(paper, ["Planning under uncertainty"])
    methods = map_paper_to_methods(paper, ["ReAct"])
    tasks = map_paper_to_tasks(paper, ["trajectory planning"])
    benchmarks = map_paper_to_benchmarks(paper, ["WebArena"])
    limitations = map_paper_to_limitations(paper, ["context limits"])
    directions = map_paper_to_directions(paper, ["long-horizon planning"])

    assert problems[0].name == "Planning under uncertainty"
    assert methods[0].name == "ReAct"
    assert tasks[0].name == "trajectory planning"
    assert benchmarks[0].name == "WebArena"
    assert limitations[0].name == "context limits"
    assert directions[0].name == "long-horizon planning"


def test_map_paper_to_paper_relationships_preserves_citation_direction() -> None:
    paper_a = Paper(paper_id="a", title="A", authors=["A"]) 
    paper_b = Paper(paper_id="b", title="B", authors=["B"]) 

    relationships = map_paper_to_paper_relationships(paper_a, cited_papers=[paper_b])
    assert len(relationships) == 1
    assert relationships[0].source_id == "a"
    assert relationships[0].target_id == "b"
    assert relationships[0].relationship_type == "cites"
    assert relationships[0].source_paper_id == "a"


def test_map_paper_to_relationships_builds_semantic_links_with_evidence() -> None:
    paper = Paper(
        paper_id="p1",
        title="Paper One",
        authors=["A"],
        year=2024,
        abstract="A planning paper.",
        venue="ICML",
        source="arxiv",
        url="https://example.com/p1",
    )

    result = map_paper_to_relationships(
        paper,
        problem_names=["Planning under uncertainty"],
        method_names=["ReAct"],
        task_names=["planning"],
        benchmark_names=["WebArena"],
        limitation_names=["context limitations"],
        direction_names=["long-horizon planning"],
        cited_papers=[Paper(paper_id="p0", title="Prior work", authors=["Z"])],
    )

    assert any(rel.relationship_type == "addresses" for rel in result.relationships)
    assert any(rel.relationship_type == "proposes" for rel in result.relationships)
    assert any(rel.relationship_type == "targets" for rel in result.relationships)
    assert any(rel.relationship_type == "evaluates_on" for rel in result.relationships)
    assert any(rel.relationship_type == "identifies" for rel in result.relationships)
    assert any(rel.relationship_type == "explored_by" for rel in result.relationships)
    assert any(rel.relationship_type == "cites" for rel in result.relationships)

    for rel in result.relationships:
        if hasattr(rel, "source_paper_id"):
            assert rel.source_paper_id == "p1"
            assert rel.evidence
            assert 0.0 <= rel.confidence <= 1.0
