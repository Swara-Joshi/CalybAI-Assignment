from __future__ import annotations

import json
import subprocess
import sys

import pytest

from src.knowledge.state import KnowledgeState
from src.models.entities import Benchmark, Limitation, Method, Paper, ResearchDirection, ResearchProblem, Task
from src.models.relationships import MethodTargetsTask, PaperAddressesProblem, PaperEvaluatesOnBenchmark, PaperIdentifiesLimitation, PaperProposesMethod, ResearchDirectionExploredByPaper, LimitationMotivatesDirection
from src.reasoning.reasoner import ProposalReasoner
from src.reasoning.proposal_parser import parse_proposal


def _build_state() -> KnowledgeState:
    state = KnowledgeState()
    paper = Paper(
        paper_id="p-llm",
        title="Persistent Memory Agents",
        authors=["Alice"],
        year=2025,
        abstract="An LLM agent with persistent memory learns from previous tool interactions.",
        venue="ICML",
        source="arxiv",
        url="https://example.com/p-llm",
    )
    problem = ResearchProblem(problem_id="prob-memory", name="persistent memory", description="The agent must retain useful context.")
    method = Method(method_id="m-memory", name="memory-augmented planning", description="Stores tool interaction history and recalls it.")
    task = Task(task_id="task-tool-use", name="tool interaction learning", description="Learn from previous tool interactions.")
    benchmark = Benchmark(benchmark_id="bench-1", name="ToolBench", description="Tool-use benchmark.")
    limitation = Limitation(limitation_id="lim-1", name="context loss", description="Without memory, actions repeat mistakes.")
    direction = ResearchDirection(direction_id="dir-1", name="persistent memory agents", description="Long-lived agent memory.")

    state.add_entity(paper)
    state.add_entity(problem)
    state.add_entity(method)
    state.add_entity(task)
    state.add_entity(benchmark)
    state.add_entity(limitation)
    state.add_entity(direction)

    state.add_relationship(PaperAddressesProblem(source_id="p-llm", target_id="prob-memory", evidence="addresses persistent memory", source_paper_id="p-llm", confidence=0.91))
    state.add_relationship(PaperProposesMethod(source_id="p-llm", target_id="m-memory", evidence="proposes memory-augmented planning", source_paper_id="p-llm", confidence=0.92))
    state.add_relationship(MethodTargetsTask(source_id="m-memory", target_id="task-tool-use", evidence="targets tool interaction learning", source_paper_id="p-llm", confidence=0.85))
    state.add_relationship(PaperEvaluatesOnBenchmark(source_id="p-llm", target_id="bench-1", evidence="evaluates on ToolBench", source_paper_id="p-llm", confidence=0.8))
    state.add_relationship(PaperIdentifiesLimitation(source_id="p-llm", target_id="lim-1", evidence="identifies context loss", source_paper_id="p-llm", confidence=0.88))
    state.add_relationship(LimitationMotivatesDirection(source_id="lim-1", target_id="dir-1", evidence="motivates persistent memory agents", source_paper_id="p-llm", confidence=0.79))
    state.add_relationship(ResearchDirectionExploredByPaper(source_id="dir-1", target_id="p-llm", evidence="explored by persistent memory agents", source_paper_id="p-llm", confidence=0.81))
    return state


def test_proposal_reasoner_matches_related_entities() -> None:
    state = _build_state()
    reasoner = ProposalReasoner(state)

    result = reasoner.reason("I propose an LLM agent with persistent memory that learns from previous tool interactions.")

    assert result["proposal_summary"]
    assert "prob-memory" in result["matched_research_problems"]
    assert "m-memory" in result["related_methods"]
    assert result["confidence"] >= 0.3
    assert result["evidence"]
    approach = result["closest_prior_approaches"][0]
    assert approach["why_relevant"]
    assert approach["problems_addressed"][0]["evidence"]["source_paper_id"] == "p-llm"
    assert approach["methods_used"][0]["name"] == "memory-augmented planning"
    assert approach["limitations_identified"][0]["name"] == "context loss"
    assert result["relevant_benchmarks"] == ["bench-1"]
    assert result["research_directions_connected_to_limitations"][0]["evidence"]
    assert "Potentially underexplored based on the selected dataset" in result["potentially_underexplored_areas"][0]["qualification"]
    assert "this is novel" not in json.dumps(result).lower()


def test_reason_script_runs_from_project_root(tmp_path) -> None:
    state_path = tmp_path / "knowledge_state.json"
    state = _build_state()
    state_path.write_text(json.dumps(state.model_dump(mode="json")), encoding="utf-8")

    proc = subprocess.run(
        [sys.executable, "scripts/reason.py", "--state", str(state_path), "--input", "persistent memory agents and tool interactions"],
        cwd="C:/Users/Swara/Desktop/Projects/CalybAI/CalybAI-Assignment/research-evolution-map",
        capture_output=True,
        text=True,
        check=False,
    )

    assert proc.returncode == 0, proc.stderr
    payload = json.loads(proc.stdout)
    assert "proposal_summary" in payload
    assert "related_methods" in payload


def test_reason_script_supports_human_output(tmp_path) -> None:
    state_path = tmp_path / "knowledge_state.json"
    state_path.write_text(json.dumps(_build_state().model_dump(mode="json")), encoding="utf-8")

    proc = subprocess.run(
        [sys.executable, "scripts/reason.py", "--state", str(state_path), "--format", "human", "--input", "persistent memory agents"],
        cwd="C:/Users/Swara/Desktop/Projects/CalybAI/CalybAI-Assignment/research-evolution-map",
        capture_output=True,
        text=True,
        check=False,
    )

    assert proc.returncode == 0, proc.stderr
    assert "Closest prior approaches:" in proc.stdout
    assert "Relevant benchmarks:" in proc.stdout
    assert "Potentially underexplored based on the selected dataset" in proc.stdout


def test_empty_proposal_is_rejected() -> None:
    with pytest.raises(ValueError, match="proposal text"):
        parse_proposal("   ")


def test_proposal_matching_does_not_match_a_concept_inside_another_word() -> None:
    state = KnowledgeState()
    state.add_entity(Paper(paper_id="p-unrelated", title="Memorable Results", authors=["A"], abstract="A memorable result."))

    result = ProposalReasoner(state).reason("An agent with memory")

    assert result["related_papers"] == []
