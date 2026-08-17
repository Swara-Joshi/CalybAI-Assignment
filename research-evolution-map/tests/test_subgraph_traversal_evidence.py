from src.knowledge.state import KnowledgeState
from src.models.entities import Method, Paper, ResearchProblem, Task
from src.models.relationships import MethodTargetsTask, PaperAddressesProblem, PaperProposesMethod
from src.reasoning.evidence import EvidenceCollector
from src.reasoning.subgraph import Subgraph
from src.reasoning.traversal import TraversalResult


def _state() -> KnowledgeState:
    state = KnowledgeState()
    for entity in (
        Paper(paper_id="p1", title="Paper", authors=["A"]),
        ResearchProblem(problem_id="problem1", name="planning"),
        Method(method_id="method1", name="planner"),
        Task(task_id="task1", name="trajectory"),
    ):
        state.add_entity(entity)
    state.add_relationship(PaperAddressesProblem(source_id="p1", target_id="problem1", evidence="paper addresses planning", source_paper_id="p1", confidence=0.9))
    state.add_relationship(PaperProposesMethod(source_id="p1", target_id="method1", evidence="paper proposes planner", source_paper_id="p1", confidence=0.8))
    state.add_relationship(MethodTargetsTask(source_id="method1", target_id="task1", evidence="planner targets trajectory", source_paper_id="p1", confidence=0.7))
    return state


def test_subgraph_contains_matched_nodes_and_incident_edges() -> None:
    summary = Subgraph(_state(), {"planning": ["problem1"]}).summary()

    assert summary["nodes"] == ["problem1"]
    assert summary["edges"] == [{"source_id": "p1", "target_id": "problem1", "relationship_type": "addresses"}]


def test_traversal_respects_depth_and_handles_cycles() -> None:
    traversal = TraversalResult(_state(), ["p1"], max_depth=2)

    assert ["p1", "method1"] in traversal.paths
    assert ["p1", "method1", "task1"] in traversal.paths
    assert all(len(path) <= 3 for path in traversal.paths)


def test_evidence_collector_returns_relationship_provenance() -> None:
    evidence = EvidenceCollector(_state()).collect(["method1"])

    assert len(evidence) == 2
    assert {item["relationship_type"] for item in evidence} == {"proposes", "targets"}
    assert all(item["evidence"] and item["source_paper_id"] == "p1" for item in evidence)