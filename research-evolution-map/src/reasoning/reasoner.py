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

        entity_collections = (
            (self.knowledge_state.research_problems, "problem_id"),
            (self.knowledge_state.methods, "method_id"),
            (self.knowledge_state.tasks, "task_id"),
            (self.knowledge_state.benchmarks, "benchmark_id"),
            (self.knowledge_state.limitations, "limitation_id"),
            (self.knowledge_state.research_directions, "direction_id"),
            (self.knowledge_state.papers, "paper_id"),
        )
        for concept in proposal.concepts:
            matches: list[str] = []
            for entities, id_field in entity_collections:
                for entity in entities:
                    searchable = " ".join(
                        str(getattr(entity, field, "") or "")
                        for field in ("name", "title", "description", "abstract")
                    ).lower()
                    if concept.lower() in searchable:
                        matches.append(str(getattr(entity, id_field)))
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
        related_paper_ids = {paper.paper_id for paper in related_papers}
        linked_target_ids = {
            relationship.target_id
            for relationship in self.knowledge_state.relationships
            if relationship.source_id in related_paper_ids
        }
        known_limitations = [
            limitation for limitation in self.knowledge_state.limitations
            if limitation.limitation_id in linked_target_ids or limitation in known_limitations
        ]
        relevant_benchmarks = [
            benchmark for benchmark in self.knowledge_state.benchmarks
            if benchmark.benchmark_id in linked_target_ids or benchmark in relevant_benchmarks
        ]
        direction_ids_from_limitations = {
            relationship.target_id
            for relationship in self.knowledge_state.relationships
            if relationship.relationship_type == "motivates" and relationship.source_id in {limitation.limitation_id for limitation in known_limitations}
        }
        research_directions = [
            direction for direction in self.knowledge_state.research_directions
            if direction.direction_id in direction_ids_from_limitations
            or direction.direction_id in linked_target_ids
            or direction in research_directions
        ]

        reasoning_paths = [
            {"path": path, "source": "knowledge-state traversal"}
            for path in traversal.paths[:10]
        ]

        confidence = min(0.99, max(0.3, 0.5 + (len(evidence_items) * 0.08)))

        relationship_evidence = self._relationship_evidence()
        prior_approaches = [
            {
                "paper_id": paper.paper_id,
                "title": paper.title,
                "year": paper.year,
                "why_relevant": self._evidence_text(relationship_evidence.get(paper.paper_id, [])),
                "problems_addressed": self._linked_entities(paper.paper_id, "addresses", self.knowledge_state.research_problems, "problem_id"),
                "methods_used": self._linked_methods(paper.paper_id),
                "limitations_identified": self._linked_entities(paper.paper_id, "identifies", self.knowledge_state.limitations, "limitation_id"),
                "evidence": relationship_evidence.get(paper.paper_id, []),
            }
            for paper in related_papers
        ]
        matched_paper_ids = {paper.paper_id for paper in related_papers}
        later_work = [
            {
                "paper_id": relationship.source_id,
                "title": self._paper_title(relationship.source_id),
                "relationship": relationship.relationship_type,
                "on_paper_id": relationship.target_id,
                "evidence": self._relationship_record(relationship),
            }
            for relationship in self.knowledge_state.relationships
            if relationship.relationship_type in {"extends", "challenges"}
            and (relationship.source_id in matched_paper_ids or relationship.target_id in matched_paper_ids)
        ]
        underexplored = self._underexplored_areas(concept_matches, related_papers, later_work)

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
            "closest_prior_approaches": prior_approaches,
            "later_work": later_work,
            "research_directions_connected_to_limitations": [
                {
                    "direction_id": direction.direction_id,
                    "name": direction.name,
                    "description": direction.description,
                    "evidence": relationship_evidence.get(direction.direction_id, []),
                }
                for direction in research_directions
            ],
            "potentially_underexplored_areas": underexplored,
            "evidence_scope": {
                "dataset_name": self.knowledge_state.metadata.dataset_name,
                "paper_count": len(self.knowledge_state.papers),
                "relationship_count": len(self.knowledge_state.relationships),
                "qualification": "Conclusions are limited to the selected knowledge state; absence of a relationship is not evidence of absence in the literature.",
            },
        }

    def _relationship_record(self, relationship: Any) -> dict[str, Any]:
        return {
            "source_id": relationship.source_id,
            "target_id": relationship.target_id,
            "relationship_type": relationship.relationship_type,
            "evidence": getattr(relationship, "evidence", ""),
            "source_paper_id": getattr(relationship, "source_paper_id", None),
            "confidence": getattr(relationship, "confidence", None),
        }

    def _relationship_evidence(self) -> dict[str, list[dict[str, Any]]]:
        result: dict[str, list[dict[str, Any]]] = {}
        for relationship in self.knowledge_state.relationships:
            record = self._relationship_record(relationship)
            for entity_id in (relationship.source_id, relationship.target_id):
                result.setdefault(entity_id, []).append(record)
        return result

    def _paper_title(self, paper_id: str) -> str | None:
        return next((paper.title for paper in self.knowledge_state.papers if paper.paper_id == paper_id), None)

    def _evidence_text(self, records: list[dict[str, Any]]) -> str:
        statements = [record["evidence"] for record in records if record["evidence"]]
        return " ".join(dict.fromkeys(statements)) or "Relevance is based on an entity match; no more specific relationship evidence is recorded."

    def _linked_entities(self, paper_id: str, relationship_type: str, entities: list[Any], id_field: str) -> list[dict[str, Any]]:
        entity_map = {getattr(entity, id_field): entity for entity in entities}
        result = []
        for relationship in self.knowledge_state.relationships:
            if relationship.source_id == paper_id and relationship.relationship_type == relationship_type and relationship.target_id in entity_map:
                entity = entity_map[relationship.target_id]
                result.append({"id": relationship.target_id, "name": getattr(entity, "name", ""), "description": getattr(entity, "description", None), "evidence": self._relationship_record(relationship)})
        return result

    def _linked_methods(self, paper_id: str) -> list[dict[str, Any]]:
        methods = {method.method_id: method for method in self.knowledge_state.methods}
        result = []
        for relationship in self.knowledge_state.relationships:
            if relationship.source_id == paper_id and relationship.relationship_type == "proposes" and relationship.target_id in methods:
                method = methods[relationship.target_id]
                result.append({"id": method.method_id, "name": method.name, "description": method.description, "targets": self._linked_entities(method.method_id, "targets", self.knowledge_state.tasks, "task_id"), "evidence": self._relationship_record(relationship)})
        return result

    def _underexplored_areas(self, concept_matches: dict[str, list[str]], related_papers: list[Any], later_work: list[dict[str, Any]]) -> list[dict[str, Any]]:
        matched_ids = sorted({entity_id for matches in concept_matches.values() for entity_id in matches})
        if not related_papers:
            area = "The proposal concepts have no matched prior paper in the selected dataset."
        elif not later_work:
            area = "No recorded prior approach links the selected concepts to documented later work."
        else:
            return []
        return [{"area": area, "qualification": "Potentially underexplored based on the selected dataset; this is not a novelty claim.", "evidence": [{"type": "dataset_observation", "matched_entity_ids": matched_ids, "matched_paper_ids": [paper.paper_id for paper in related_papers], "later_work_count": len(later_work)}]}]
