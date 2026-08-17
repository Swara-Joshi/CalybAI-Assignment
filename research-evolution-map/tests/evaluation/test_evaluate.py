from __future__ import annotations

import json

import pytest

from scripts.evaluate import evaluate
from src.knowledge.state import KnowledgeState
from src.models.entities import Benchmark, Method, Paper, ResearchProblem, Task
from src.models.relationships import MethodTargetsTask, PaperAddressesProblem, PaperProposesMethod


def _state() -> KnowledgeState:
    state = KnowledgeState()
    for entity in (
        Paper(paper_id="p-llm", title="Persistent Memory Agents", authors=["A"], abstract="An LLM agent with persistent memory learns from previous tool interactions."),
        Paper(paper_id="p-planning", title="ReAct Planning", authors=["B"], abstract="ReAct addresses planning under uncertainty."),
        ResearchProblem(problem_id="prob-memory", name="persistent memory"),
        ResearchProblem(problem_id="prob-planning", name="planning under uncertainty"),
        Method(method_id="m-memory", name="memory-augmented planning", description="Stores tool interaction history."),
        Method(method_id="m-react", name="ReAct"),
        Task(task_id="task-planning", name="planning task"),
        Benchmark(benchmark_id="bench-1", name="ToolBench"),
    ):
        state.add_entity(entity)
    state.add_relationship(PaperAddressesProblem(source_id="p-llm", target_id="prob-memory", evidence="addresses persistent memory", source_paper_id="p-llm", confidence=0.9))
    state.add_relationship(PaperProposesMethod(source_id="p-llm", target_id="m-memory", evidence="proposes memory method", source_paper_id="p-llm", confidence=0.9))
    state.add_relationship(PaperAddressesProblem(source_id="p-planning", target_id="prob-planning", evidence="addresses planning", source_paper_id="p-planning", confidence=0.9))
    state.add_relationship(PaperProposesMethod(source_id="p-planning", target_id="m-react", evidence="proposes ReAct", source_paper_id="p-planning", confidence=0.9))
    state.add_relationship(MethodTargetsTask(source_id="m-react", target_id="task-planning", evidence="targets planning", source_paper_id="p-planning", confidence=0.8))
    return state


def _dataset() -> dict:
    return json.loads((__import__("pathlib").Path("data/evaluation/proposals.json")).read_text(encoding="utf-8"))


def test_holdout_evaluation_produces_all_requested_metrics() -> None:
    report = evaluate(_dataset(), _state())

    assert report["proposal_count"] == 3
    assert set(report["averages"]) == {
        "prior_paper_identification", "method_identification", "research_problem_identification",
        "relationship_traversal_correctness", "evidence_grounding", "unsupported_conclusion_rate",
        "structured_output_validity",
    }
    assert report["averages"]["structured_output_validity"] == 1.0
    assert report["averages"]["evidence_grounding"] > 0.0
    assert len(report["representative_examples"]) == 3


def test_evaluation_rejects_construction_dataset() -> None:
    dataset = _dataset()
    dataset["dataset_type"] = "knowledge_construction"

    with pytest.raises(ValueError, match="new_proposal_holdout"):
        evaluate(dataset, _state())


def test_evaluation_rejects_proposal_id_that_is_a_construction_paper() -> None:
    dataset = _dataset()
    dataset["proposals"][0]["proposal_id"] = "p-llm"

    with pytest.raises(ValueError, match="overlaps construction paper"):
        evaluate(dataset, _state())