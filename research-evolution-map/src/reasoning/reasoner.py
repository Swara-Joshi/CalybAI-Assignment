from __future__ import annotations

from typing import Any

from src.knowledge.state import KnowledgeState
from src.reasoning.evidence import EvidenceCollector
from src.reasoning.proposal_parser import parse_proposal
from src.reasoning.subgraph import Subgraph
from src.reasoning.traversal import TraversalResult


class ProposalReasoner:
    """Deterministic reasoning engine using explicit knowledge-state relationships."""

    def __init__(self, knowledge_state: KnowledgeState) -> None:
        self.knowledge_state = knowledge_state

    def reason(self, proposal_text: str) -> dict[str, Any]:
        proposal = parse_proposal(proposal_text)
        concept_matches: dict[str, list[str]] = {}

        for concept in proposal.concepts:
            matches: list[str] = []
            for problem in self.knowledge_state.research_problems:
                if concept.lower() in problem.name.lower() or concept.lower() in (problem.description or "").lower():
                    matches.append(problem.problem_id)
            for method in self.knowledge_state.methods:
                if concept.lower() in method.name.lower() or concept.lower() in (method.description or "").lower():
                    matches.append(method.method_id)
            for paper in self.knowledge_state.papers:
                if concept.lower() in paper.title.lower() or concept.lower() in (paper.abstract or "").lower():
                    matches.append(paper.paper_id)
            if matches:
                concept_matches[concept] = matches

        if not concept_matches:
            concept_matches = {concept: [] for concept in proposal.concepts}

        subgraph = Subgraph(self.knowledge_state, concept_matches)
        start_nodes = sorted({node for matches in concept_matches.values() for node in matches})
        traversal = TraversalResult(self.knowledge_state, start_nodes, max_depth=2)

        evidence = EvidenceCollector(self.knowledge_state)
        evidence_items = evidence.collect(start_nodes)

        related_methods = [
            method for method in self.knowledge_state.methods
            if any(method.method_id in matches for matches in concept_matches.values())
        ]
        related_papers = [
            paper for paper in self.knowledge_state.papers
            if any(paper.paper_id in matches for matches in concept_matches.values())
        ]
        known_limitations = [
            limitation for limitation in self.knowledge_state.limitations
            if any(limitation.limitation_id in matches for matches in concept_matches.values())
        ]
        relevant_benchmarks = [
            benchmark for benchmark in self.knowledge_state.benchmarks
            if any(benchmark.benchmark_id in matches for matches in concept_matches.values())
        ]
        research_directions = [
            direction for direction in self.knowledge_state.research_directions
            if any(direction.direction_id in matches for matches in concept_matches.values())
        ]

        reasoning_paths = [
            {"path": path, "source": "knowledge-state traversal"}
            for path in traversal.paths[:10]
        ]

        confidence = min(0.99, max(0.3, 0.5 + (len(evidence_items) * 0.08)))

        return {
            "proposal_summary": proposal.text,
            "matched_research_problems": [
                problem.problem_id for problem in self.knowledge_state.research_problems
                if any(problem.problem_id in matches for matches in concept_matches.values())
            ],
            "related_methods": [method.method_id for method in related_methods],
            "related_papers": [paper.paper_id for paper in related_papers],
            "known_limitations": [limitation.limitation_id for limitation in known_limitations],
            "relevant_benchmarks": [benchmark.benchmark_id for benchmark in relevant_benchmarks],
            "research_directions": [direction.direction_id for direction in research_directions],
            "reasoning_paths": reasoning_paths,
            "evidence": evidence_items,
            "confidence": round(confidence, 2),
        }
