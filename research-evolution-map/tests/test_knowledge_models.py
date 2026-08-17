import pytest
from pydantic import ValidationError

from src.models.entities import (
    Benchmark,
    Limitation,
    Method,
    Paper,
    ResearchDirection,
    ResearchProblem,
    Task,
)
from src.models.knowledge_state import KnowledgeState
from src.models.relationships import (
    BaseRelationship,
    LimitationMotivatesDirection,
    MethodImprovesUponMethod,
    PaperAddressesProblem,
    PaperCitesPaper,
    PaperChallengesPaper,
    PaperEvaluatesOnBenchmark,
    PaperExtendsPaper,
    PaperIdentifiesLimitation,
    PaperProposesMethod,
    ResearchDirectionExploredByPaper,
    validate_relationship_compatibility,
)


def test_entities_validate_minimal_fields() -> None:
    paper = Paper(
        paper_id="p1",
        title="A paper",
        authors=["Alice", "Bob"],
        year=2024,
        abstract="Abstract",
        venue="ICML",
        source="arxiv",
        url="https://example.com/p1",
    )

    assert paper.paper_id == "p1"

    problem = ResearchProblem(problem_id="prob1", name="Planning", description="Need planning")
    method = Method(method_id="m1", name="ReAct", description="Method")
    task = Task(task_id="task1", name="Trajectory planning", description="Task")
    benchmark = Benchmark(benchmark_id="bench1", name="WebArena", description="Benchmark")
    limitation = Limitation(limitation_id="lim1", name="Context limits", description="Issue")
    direction = ResearchDirection(direction_id="dir1", name="Long-horizon planning", description="Direction")

    assert problem.problem_id == "prob1"
    assert method.name == "ReAct"
    assert task.task_id == "task1"
    assert benchmark.name == "WebArena"
    assert limitation.name == "Context limits"
    assert direction.name == "Long-horizon planning"


def test_relationship_models() -> None:
    rel = PaperAddressesProblem(
        source_id="paper-1",
        target_id="problem-1",
        evidence="The paper frames the challenge.",
        source_paper_id="paper-1",
        confidence=0.93,
    )
    assert rel.relationship_type == "addresses"

    cites = PaperCitesPaper(
        source_id="paper-1",
        target_id="paper-2",
        evidence="This paper cites the earlier work.",
        source_paper_id="paper-1",
        confidence=0.82,
    )
    assert cites.relationship_type == "cites"


def test_relationship_compatibility_validation() -> None:
    paper = Paper(paper_id="p1", title="Alpha", authors=["A"])
    method = Method(method_id="m1", name="ReAct")
    problem = ResearchProblem(problem_id="prob1", name="Planning")
    benchmark = Benchmark(benchmark_id="b1", name="Bench")
    limitation = Limitation(limitation_id="l1", name="Issue")
    direction = ResearchDirection(direction_id="d1", name="Direction")
    task = Task(task_id="t1", name="Task")

    validate_relationship_compatibility(paper, problem, "addresses")
    validate_relationship_compatibility(paper, method, "proposes")
    validate_relationship_compatibility(method, task, "targets")
    validate_relationship_compatibility(paper, benchmark, "evaluates_on")
    validate_relationship_compatibility(paper, limitation, "identifies")
    validate_relationship_compatibility(paper, paper, "extends")
    validate_relationship_compatibility(paper, paper, "challenges")
    validate_relationship_compatibility(method, method, "improves_upon")
    validate_relationship_compatibility(limitation, direction, "motivates")
    validate_relationship_compatibility(direction, paper, "explored_by")
    validate_relationship_compatibility(paper, paper, "cites")

    with pytest.raises(ValueError):
        validate_relationship_compatibility(paper, method, "addresses")

    with pytest.raises(ValueError):
        validate_relationship_compatibility(problem, paper, "cites")


def test_knowledge_state_adds_entities_and_relationships() -> None:
    state = KnowledgeState()

    paper = Paper(paper_id="p1", title="Paper 1", authors=["A"])
    problem = ResearchProblem(problem_id="prob1", name="Planning")
    method = Method(method_id="m1", name="ReAct")
    task = Task(task_id="t1", name="Task")
    benchmark = Benchmark(benchmark_id="b1", name="Bench")
    limitation = Limitation(limitation_id="l1", name="Issue")
    direction = ResearchDirection(direction_id="d1", name="Direction")

    for entity in (paper, problem, method, task, benchmark, limitation, direction):
        state.add_entity(entity)

    relationship = PaperAddressesProblem(
        source_id="p1",
        target_id="prob1",
        evidence="The paper addresses planning.",
        source_paper_id="p1",
        confidence=0.9,
    )
    state.add_relationship(relationship)

    assert state.statistics()["relationships"] == 1
    assert state.papers[0].paper_id == "p1"

    with pytest.raises(ValueError):
        state.add_relationship(
            BaseRelationship(source_id="missing", target_id="prob1", relationship_type="addresses")
        )


def test_invalid_relationship_values_are_rejected() -> None:
    with pytest.raises(ValidationError):
        PaperAddressesProblem(
            source_id="p1",
            target_id="prob1",
            evidence="",
            source_paper_id="p1",
            confidence=1.2,
        )

    with pytest.raises(ValueError):
        validate_relationship_compatibility(
            Paper(paper_id="p1", title="P", authors=["A"]),
            Method(method_id="m1", name="M"),
            "cites",
        )
