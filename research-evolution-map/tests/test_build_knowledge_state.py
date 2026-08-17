from scripts.build_knowledge_state import _build_state_from_papers
from src.models.entities import Paper


def test_build_state_from_papers_constructs_entities_and_evidence_relationships() -> None:
    state = _build_state_from_papers(
        [Paper(paper_id="p1", title="Planning Paper", authors=["A"], year=2024)]
    )

    assert state.metadata.dataset_name == "research-evolution-map"
    assert state.metadata.paper_count == 1
    assert len(state.papers) == 1
    assert state.research_problems[0].name == "planning under uncertainty"
    assert any(relationship.evidence for relationship in state.relationships)


def test_build_state_from_papers_handles_empty_input() -> None:
    state = _build_state_from_papers([])

    assert state.statistics() == {
        "papers": 0,
        "research_problems": 0,
        "methods": 0,
        "tasks": 0,
        "benchmarks": 0,
        "limitations": 0,
        "research_directions": 0,
        "relationships": 0,
    }