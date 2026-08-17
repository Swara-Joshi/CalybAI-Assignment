from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from src.models.entities import (
    Benchmark,
    Limitation,
    Method,
    Paper,
    ResearchDirection,
    ResearchProblem,
    Task,
)
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
    MethodTargetsTask,
)


@dataclass
class MappingResult:
    """Structured output from mapping a paper into knowledge entities and relationships."""

    paper: Paper
    entities: list[Any]
    relationships: list[BaseRelationship]


def _semantic_evidence(paper: Paper, label: str) -> str:
    return f"{paper.title}: {label}"


def deterministic_metadata_mapping(paper: Paper) -> dict[str, Any]:
    """Map deterministic metadata from a normalized paper into canonical entity fields."""
    return {
        "paper_id": paper.paper_id,
        "title": paper.title,
        "authors": paper.authors,
        "year": paper.year,
        "abstract": paper.abstract,
        "venue": paper.venue,
        "source": paper.source,
        "url": paper.url,
    }


def map_paper_to_problems(paper: Paper, problem_names: list[str] | None = None) -> list[ResearchProblem]:
    """Create a research problem entity from explicit metadata or TODO logic."""
    problem_names = problem_names or []
    if not problem_names:
        return []
    return [
        ResearchProblem(
            problem_id=f"{paper.paper_id}-problem-{idx}",
            name=name,
            description=f"TODO: explicit problem interpretation for {paper.title}",
        )
        for idx, name in enumerate(problem_names)
    ]


def map_paper_to_methods(paper: Paper, method_names: list[str] | None = None) -> list[Method]:
    """Create a method entity from explicit metadata or TODO logic."""
    method_names = method_names or []
    if not method_names:
        return []
    return [
        Method(
            method_id=f"{paper.paper_id}-method-{idx}",
            name=name,
            description=f"TODO: explicit method interpretation for {paper.title}",
        )
        for idx, name in enumerate(method_names)
    ]


def map_paper_to_tasks(paper: Paper, task_names: list[str] | None = None) -> list[Task]:
    """Create task entities from explicit metadata or TODO logic."""
    task_names = task_names or []
    if not task_names:
        return []
    return [
        Task(
            task_id=f"{paper.paper_id}-task-{idx}",
            name=name,
            description=f"TODO: explicit task interpretation for {paper.title}",
        )
        for idx, name in enumerate(task_names)
    ]


def map_paper_to_benchmarks(paper: Paper, benchmark_names: list[str] | None = None) -> list[Benchmark]:
    """Create benchmark entities from explicit metadata or TODO logic."""
    benchmark_names = benchmark_names or []
    if not benchmark_names:
        return []
    return [
        Benchmark(
            benchmark_id=f"{paper.paper_id}-benchmark-{idx}",
            name=name,
            description=f"TODO: explicit benchmark interpretation for {paper.title}",
        )
        for idx, name in enumerate(benchmark_names)
    ]


def map_paper_to_limitations(paper: Paper, limitation_names: list[str] | None = None) -> list[Limitation]:
    """Create limitation entities from explicit metadata or TODO logic."""
    limitation_names = limitation_names or []
    if not limitation_names:
        return []
    return [
        Limitation(
            limitation_id=f"{paper.paper_id}-limitation-{idx}",
            name=name,
            description=f"TODO: explicit limitation interpretation for {paper.title}",
        )
        for idx, name in enumerate(limitation_names)
    ]


def map_paper_to_directions(paper: Paper, direction_names: list[str] | None = None) -> list[ResearchDirection]:
    """Create research direction entities from explicit metadata or TODO logic."""
    direction_names = direction_names or []
    if not direction_names:
        return []
    return [
        ResearchDirection(
            direction_id=f"{paper.paper_id}-direction-{idx}",
            name=name,
            description=f"TODO: explicit research direction interpretation for {paper.title}",
        )
        for idx, name in enumerate(direction_names)
    ]


def map_paper_to_paper_relationships(
    paper: Paper,
    cited_papers: list[Paper] | None = None,
    extended_papers: list[Paper] | None = None,
    challenged_papers: list[Paper] | None = None,
) -> list[BaseRelationship]:
    """Map internal citation and paper-to-paper relationships."""
    relationships: list[BaseRelationship] = []

    for cited in cited_papers or []:
        relationships.append(
            PaperCitesPaper(
                source_id=paper.paper_id,
                target_id=cited.paper_id,
                evidence=_semantic_evidence(paper, f"cites {cited.title}"),
                source_paper_id=paper.paper_id,
                confidence=0.95,
            )
        )

    for extended in extended_papers or []:
        relationships.append(
            PaperExtendsPaper(
                source_id=paper.paper_id,
                target_id=extended.paper_id,
                evidence=_semantic_evidence(paper, f"extends {extended.title}"),
                source_paper_id=paper.paper_id,
                confidence=0.9,
            )
        )

    for challenged in challenged_papers or []:
        relationships.append(
            PaperChallengesPaper(
                source_id=paper.paper_id,
                target_id=challenged.paper_id,
                evidence=_semantic_evidence(paper, f"challenges {challenged.title}"),
                source_paper_id=paper.paper_id,
                confidence=0.9,
            )
        )

    return relationships


def map_paper_to_relationships(
    paper: Paper,
    *,
    problem_names: list[str] | None = None,
    method_names: list[str] | None = None,
    task_names: list[str] | None = None,
    benchmark_names: list[str] | None = None,
    limitation_names: list[str] | None = None,
    direction_names: list[str] | None = None,
    cited_papers: list[Paper] | None = None,
    extended_papers: list[Paper] | None = None,
    challenged_papers: list[Paper] | None = None,
) -> MappingResult:
    """Map a normalized paper into explicit entities and relationships for the fixed schema."""
    entities: list[Any] = []
    relationships: list[BaseRelationship] = []

    entities.extend(map_paper_to_problems(paper, problem_names))
    entities.extend(map_paper_to_methods(paper, method_names))
    entities.extend(map_paper_to_tasks(paper, task_names))
    entities.extend(map_paper_to_benchmarks(paper, benchmark_names))
    entities.extend(map_paper_to_limitations(paper, limitation_names))
    entities.extend(map_paper_to_directions(paper, direction_names))

    # Deterministic metadata mapping uses the paper itself.
    entities.append(paper)

    for problem in map_paper_to_problems(paper, problem_names):
        relationships.append(
            PaperAddressesProblem(
                source_id=paper.paper_id,
                target_id=problem.problem_id,
                evidence=_semantic_evidence(paper, f"addresses {problem.name}"),
                source_paper_id=paper.paper_id,
                confidence=0.9,
            )
        )

    for method in map_paper_to_methods(paper, method_names):
        relationships.append(
            PaperProposesMethod(
                source_id=paper.paper_id,
                target_id=method.method_id,
                evidence=_semantic_evidence(paper, f"proposes {method.name}"),
                source_paper_id=paper.paper_id,
                confidence=0.9,
            )
        )

    for method in map_paper_to_methods(paper, method_names):
        for task_name in task_names or []:
            task = Task(task_id=f"{paper.paper_id}-task-{task_names.index(task_name)}", name=task_name)
            relationships.append(
                MethodTargetsTask(
                    source_id=method.method_id,
                    target_id=task.task_id,
                    evidence=_semantic_evidence(paper, f"targets {task.name}"),
                    source_paper_id=paper.paper_id,
                    confidence=0.8,
                )
            )

    for benchmark in map_paper_to_benchmarks(paper, benchmark_names):
        relationships.append(
            PaperEvaluatesOnBenchmark(
                source_id=paper.paper_id,
                target_id=benchmark.benchmark_id,
                evidence=_semantic_evidence(paper, f"evaluates on {benchmark.name}"),
                source_paper_id=paper.paper_id,
                confidence=0.9,
            )
        )

    for limitation in map_paper_to_limitations(paper, limitation_names):
        relationships.append(
            PaperIdentifiesLimitation(
                source_id=paper.paper_id,
                target_id=limitation.limitation_id,
                evidence=_semantic_evidence(paper, f"identifies {limitation.name}"),
                source_paper_id=paper.paper_id,
                confidence=0.9,
            )
        )

    for direction in map_paper_to_directions(paper, direction_names):
        relationships.append(
            ResearchDirectionExploredByPaper(
                source_id=direction.direction_id,
                target_id=paper.paper_id,
                evidence=_semantic_evidence(paper, f"explored by {paper.title}"),
                source_paper_id=paper.paper_id,
                confidence=0.8,
            )
        )

    for limitation in map_paper_to_limitations(paper, limitation_names):
        for direction in map_paper_to_directions(paper, direction_names):
            relationships.append(
                LimitationMotivatesDirection(
                    source_id=limitation.limitation_id,
                    target_id=direction.direction_id,
                    evidence=_semantic_evidence(paper, f"motivation for {direction.name}"),
                    source_paper_id=paper.paper_id,
                    confidence=0.8,
                )
            )

    relationships.extend(map_paper_to_paper_relationships(
        paper,
        cited_papers=cited_papers,
        extended_papers=extended_papers,
        challenged_papers=challenged_papers,
    ))

    return MappingResult(paper=paper, entities=entities, relationships=relationships)
