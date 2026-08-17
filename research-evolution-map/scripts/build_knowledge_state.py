from __future__ import annotations

import json
import re
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from src.knowledge.mapping import map_paper_to_relationships
from src.knowledge.serializer import KnowledgeStateSerializer
from src.knowledge.state import KnowledgeState
from src.knowledge.validator import validate_knowledge_state
from src.models.entities import (
    Benchmark,
    Limitation,
    Method,
    Paper,
    ResearchDirection,
    ResearchProblem,
    Task,
)
from src.models.relationships import BaseRelationship


def _canonical_name(value: str) -> str:
    text = re.sub(r"[^a-z0-9]+", " ", value.lower()).strip()
    return re.sub(r"\s+", " ", text)


def _deduplicate_entities(entities: list[Any], entity_type: str) -> list[Any]:
    seen: dict[str, Any] = {}
    for entity in entities:
        if entity_type == "methods":
            key = _canonical_name(entity.name)
            if key not in seen:
                seen[key] = entity
        elif entity_type == "research_problems":
            key = _canonical_name(entity.name)
            if key not in seen:
                seen[key] = entity
        elif entity_type == "tasks":
            key = _canonical_name(entity.name)
            if key not in seen:
                seen[key] = entity
        elif entity_type == "benchmarks":
            key = _canonical_name(entity.name)
            if key not in seen:
                seen[key] = entity
        elif entity_type == "limitations":
            key = _canonical_name(entity.name)
            if key not in seen:
                seen[key] = entity
        elif entity_type == "research_directions":
            key = _canonical_name(entity.name)
            if key not in seen:
                seen[key] = entity
    return list(seen.values())


def _build_state_from_papers(papers: list[Paper]) -> KnowledgeState:
    state = KnowledgeState()
    for paper in papers:
        state.add_entity(paper)

    problem_entities: list[ResearchProblem] = []
    method_entities: list[Method] = []
    task_entities: list[Task] = []
    benchmark_entities: list[Benchmark] = []
    limitation_entities: list[Limitation] = []
    direction_entities: list[ResearchDirection] = []
    relationships: list[BaseRelationship] = []

    for paper in papers:
        result = map_paper_to_relationships(
            paper,
            problem_names=["planning under uncertainty"],
            method_names=["ReAct"],
            task_names=["task planning"],
            benchmark_names=["WebArena"],
            limitation_names=["context limits"],
            direction_names=["long-horizon planning"],
            cited_papers=[],
        )

        for entity in result.entities:
            if isinstance(entity, ResearchProblem):
                problem_entities.append(entity)
            elif isinstance(entity, Method):
                method_entities.append(entity)
            elif isinstance(entity, Task):
                task_entities.append(entity)
            elif isinstance(entity, Benchmark):
                benchmark_entities.append(entity)
            elif isinstance(entity, Limitation):
                limitation_entities.append(entity)
            elif isinstance(entity, ResearchDirection):
                direction_entities.append(entity)

        relationships.extend(result.relationships)

    for entity in _deduplicate_entities(problem_entities, "research_problems"):
        state.research_problems.append(entity)
    for entity in _deduplicate_entities(method_entities, "methods"):
        state.methods.append(entity)
    for entity in _deduplicate_entities(task_entities, "tasks"):
        state.tasks.append(entity)
    for entity in _deduplicate_entities(benchmark_entities, "benchmarks"):
        state.benchmarks.append(entity)
    for entity in _deduplicate_entities(limitation_entities, "limitations"):
        state.limitations.append(entity)
    for entity in _deduplicate_entities(direction_entities, "research_directions"):
        state.research_directions.append(entity)

    for relationship in relationships:
        state.add_relationship(relationship)

    state.metadata.dataset_name = "research-evolution-map"
    state.metadata.source_information = {"source": "normalized paper mapping", "generation": "deterministic"}
    return state


def _load_papers_from_processed() -> list[Paper]:
    project_root = Path(__file__).resolve().parents[1]
    processed_dir = project_root / "data" / "processed"
    candidate_files = sorted(processed_dir.glob("*.json"))
    if not candidate_files:
        raise FileNotFoundError(f"No processed paper JSON files found in {processed_dir}")
    latest = candidate_files[-1]
    payload = json.loads(latest.read_text(encoding="utf-8"))
    return [Paper.model_validate(entry) for entry in payload]


def _print_statistics(state: KnowledgeState, invalid_relationships: list[str], missing_evidence: list[str]) -> None:
    counts = Counter(rel.relationship_type for rel in state.relationships)
    print("papers:", len(state.papers))
    print("entities by type:")
    print("  papers:", len(state.papers))
    print("  research_problems:", len(state.research_problems))
    print("  methods:", len(state.methods))
    print("  tasks:", len(state.tasks))
    print("  benchmarks:", len(state.benchmarks))
    print("  limitations:", len(state.limitations))
    print("  research_directions:", len(state.research_directions))
    print("relationships by type:")
    for rel_type, count in sorted(counts.items()):
        print(f"  {rel_type}: {count}")
    print("invalid relationships:", len(invalid_relationships))
    for item in invalid_relationships:
        print("  -", item)
    print("relationships missing evidence:", len(missing_evidence))
    for item in missing_evidence:
        print("  -", item)


def main() -> None:
    project_root = Path(__file__).resolve().parents[1]
    processed_root = project_root / "data" / "processed"
    processed_root.mkdir(parents=True, exist_ok=True)

    papers = _load_papers_from_processed()
    state = _build_state_from_papers(papers)

    validation_errors = validate_knowledge_state(state)
    missing_evidence = [
        f"{rel.source_id}->{rel.target_id}:{rel.relationship_type}"
        for rel in state.relationships
        if isinstance(rel, BaseRelationship) and getattr(rel, "evidence", None) in (None, "")
    ]

    mapping_result = {
        "papers": [paper.model_dump(mode="json") for paper in state.papers],
        "entities_by_type": {
            "papers": len(state.papers),
            "research_problems": len(state.research_problems),
            "methods": len(state.methods),
            "tasks": len(state.tasks),
            "benchmarks": len(state.benchmarks),
            "limitations": len(state.limitations),
            "research_directions": len(state.research_directions),
        },
        "relationships_by_type": dict(sorted(Counter(rel.relationship_type for rel in state.relationships).items())),
        "invalid_relationships": validation_errors,
        "relationships_missing_evidence": missing_evidence,
    }
    (processed_root / "mapping_results.json").write_text(json.dumps(mapping_result, indent=2, ensure_ascii=False), encoding="utf-8")

    serializer = KnowledgeStateSerializer(project_root / "data" / "knowledge_state" / "knowledge_state.json")
    serializer.save(state)

    _print_statistics(state, validation_errors, missing_evidence)


if __name__ == "__main__":
    main()
