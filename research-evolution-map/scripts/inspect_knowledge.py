from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.knowledge.serializer import load_knowledge_state


def _load_state(path: Path):
    return load_knowledge_state(path)


def _print_summary(state) -> None:
    print("Number of papers:", len(state.papers))
    print("Number of research problems:", len(state.research_problems))
    print("Number of methods:", len(state.methods))
    print("Number of tasks:", len(state.tasks))
    print("Number of benchmarks:", len(state.benchmarks))
    print("Number of limitations:", len(state.limitations))
    print("Number of research directions:", len(state.research_directions))

    rel_counts = Counter(rel.relationship_type for rel in state.relationships)
    print("Number of relationships by type:")
    for rel_type, count in sorted(rel_counts.items()):
        print(f"  {rel_type}: {count}")

    print("Most cited papers:")
    incoming = Counter(rel.target_id for rel in state.relationships if rel.relationship_type == "cites")
    for paper_id, count in incoming.most_common(10):
        paper = next((p for p in state.papers if p.paper_id == paper_id), None)
        title = paper.title if paper else paper_id
        print(f"  {paper_id} ({title}): {count}")

    print("Most connected methods:")
    method_connections = Counter()
    for rel in state.relationships:
        if rel.relationship_type in {"proposes", "improves_upon", "targets"}:
            if rel.relationship_type == "proposes":
                method_connections[rel.target_id] += 1
            elif rel.relationship_type == "improves_upon":
                method_connections[rel.source_id] += 1
                method_connections[rel.target_id] += 1
            elif rel.relationship_type == "targets":
                method_connections[rel.source_id] += 1
    for method_id, count in method_connections.most_common(10):
        method = next((m for m in state.methods if m.method_id == method_id), None)
        name = method.name if method else method_id
        print(f"  {method_id} ({name}): {count}")

    print("Most common research problems:")
    problem_counts = Counter()
    for rel in state.relationships:
        if rel.relationship_type == "addresses":
            problem_counts[rel.target_id] += 1
    for problem_id, count in problem_counts.most_common(10):
        problem = next((p for p in state.research_problems if p.problem_id == problem_id), None)
        name = problem.name if problem else problem_id
        print(f"  {problem_id} ({name}): {count}")

    print("Research directions with the most supporting papers:")
    direction_support = Counter()
    for rel in state.relationships:
        if rel.relationship_type == "explored_by":
            direction_support[rel.source_id] += 1
    for direction_id, count in direction_support.most_common(10):
        direction = next((d for d in state.research_directions if d.direction_id == direction_id), None)
        name = direction.name if direction else direction_id
        print(f"  {direction_id} ({name}): {count}")

    print("Example multi hop relationship paths:")
    paths = []
    for paper in state.papers[:10]:
        for rel in state.relationships:
            if rel.relationship_type == "proposes" and rel.source_id == paper.paper_id:
                method_id = rel.target_id
                for rel2 in state.relationships:
                    if rel2.relationship_type == "targets" and rel2.source_id == method_id:
                        task_id = rel2.target_id
                        paths.append((paper.paper_id, method_id, task_id))
    for path in paths[:10]:
        print("  -", " -> ".join(path))
    if not paths:
        print("  - none")


def _print_paper_details(state, paper_id: str) -> None:
    paper = next((p for p in state.papers if p.paper_id == paper_id), None)
    if paper is None:
        print(f"Paper not found: {paper_id}")
        return

    print(f"Paper: {paper.paper_id} | {paper.title}")
    print(f"Authors: {', '.join(paper.authors) if paper.authors else 'Unknown'}")
    print(f"Year: {paper.year}")
    print(f"Venue: {paper.venue}")
    print(f"Source: {paper.source}")
    print(f"URL: {paper.url}")

    incoming = [rel for rel in state.relationships if rel.target_id == paper.paper_id]
    outgoing = [rel for rel in state.relationships if rel.source_id == paper.paper_id]
    print("Incoming relationships:")
    for rel in incoming:
        print(f"  {rel.relationship_type}: {rel.source_id} -> {rel.target_id}")
    print("Outgoing relationships:")
    for rel in outgoing:
        print(f"  {rel.relationship_type}: {rel.source_id} -> {rel.target_id}")


def _print_method_details(state, method_id: str) -> None:
    method = next((m for m in state.methods if m.method_id == method_id), None)
    if method is None:
        print(f"Method not found: {method_id}")
        return

    print(f"Method: {method.method_id} | {method.name}")
    print(f"Description: {method.description}")

    incoming = [rel for rel in state.relationships if rel.target_id == method_id]
    outgoing = [rel for rel in state.relationships if rel.source_id == method_id]
    print("Incoming relationships:")
    for rel in incoming:
        print(f"  {rel.relationship_type}: {rel.source_id} -> {rel.target_id}")
    print("Outgoing relationships:")
    for rel in outgoing:
        print(f"  {rel.relationship_type}: {rel.source_id} -> {rel.target_id}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Inspect the serialized knowledge state.")
    parser.add_argument("--state", default="data/knowledge_state/knowledge_state.json", help="Path to the serialized knowledge state JSON file.")
    parser.add_argument("--paper-id", help="Inspect a specific paper by ID.")
    parser.add_argument("--method-id", help="Inspect a specific method by ID.")
    args = parser.parse_args()

    state_path = Path(args.state)
    state = _load_state(state_path)

    if args.paper_id:
        _print_paper_details(state, args.paper_id)
        return

    if args.method_id:
        _print_method_details(state, args.method_id)
        return

    _print_summary(state)


if __name__ == "__main__":
    main()
