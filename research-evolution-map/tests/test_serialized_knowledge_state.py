import json

import pytest
from pydantic import ValidationError

from src.knowledge.serializer import KnowledgeStateSerializer
from src.knowledge.state import KnowledgeState, StateMetadata
from src.models.entities import Benchmark, Method, Paper, ResearchDirection, ResearchProblem, Task, Limitation
from src.models.relationships import PaperAddressesProblem, PaperProposesMethod


def _build_state() -> KnowledgeState:
    state = KnowledgeState()
    paper = Paper(paper_id="p1", title="Paper 1", authors=["A"], year=2024)
    problem = ResearchProblem(problem_id="prob1", name="Planning")
    method = Method(method_id="m1", name="ReAct")
    task = Task(task_id="t1", name="Planning task")
    benchmark = Benchmark(benchmark_id="bench1", name="WebArena")
    limitation = Limitation(limitation_id="lim1", name="Context limits")
    direction = ResearchDirection(direction_id="dir1", name="Long-horizon planning")

    for entity in (paper, problem, method, task, benchmark, limitation, direction):
        state.add_entity(entity)

    state.add_relationship(
        PaperAddressesProblem(
            source_id="p1",
            target_id="prob1",
            evidence="Paper frames a core planning problem.",
            source_paper_id="p1",
            confidence=0.95,
        )
    )
    state.add_relationship(
        PaperProposesMethod(
            source_id="p1",
            target_id="m1",
            evidence="Paper introduces the method.",
            source_paper_id="p1",
            confidence=0.91,
        )
    )
    return state


def test_knowledge_state_serializes_and_deserializes(tmp_path) -> None:
    state = _build_state()
    serializer = KnowledgeStateSerializer(tmp_path / "knowledge_state.json")

    output_path = serializer.save(state)
    assert output_path.exists()

    loaded = serializer.load()
    assert loaded.metadata.paper_count == 1
    assert len(loaded.papers) == 1
    assert len(loaded.relationships) == 2
    assert loaded.relationships[0].evidence == "Paper frames a core planning problem."
    assert loaded.relationships[0].confidence == 0.95


def test_invalid_relationship_is_rejected_after_load(tmp_path) -> None:
    state = _build_state()
    bad_relationship = PaperAddressesProblem(
        source_id="missing",
        target_id="prob1",
        evidence="Bad source",
        source_paper_id="p1",
        confidence=0.8,
    )
    state.add_relationship(bad_relationship)

    serializer = KnowledgeStateSerializer(tmp_path / "bad_state.json")
    with pytest.raises(ValueError):
        serializer.save(state)


def test_knowledge_state_json_schema_metadata_is_present(tmp_path) -> None:
    state = _build_state()
    serializer = KnowledgeStateSerializer(tmp_path / "knowledge_state.json")
    serializer.save(state)

    payload = json.loads((tmp_path / "knowledge_state.json").read_text(encoding="utf-8"))
    assert payload["metadata"]["schema_version"] == "1.0"
    assert payload["metadata"]["dataset_name"] == "research-evolution-map"
    assert payload["metadata"]["paper_count"] == 1
    assert payload["metadata"]["generated_at"]
