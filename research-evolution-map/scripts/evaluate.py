from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.knowledge.serializer import load_knowledge_state
from src.reasoning.reasoner import ProposalReasoner


RESULT_KEYS = {
    "proposal_summary", "matched_research_problems", "related_methods", "related_papers",
    "known_limitations", "relevant_benchmarks", "research_directions", "reasoning_paths",
    "evidence", "confidence", "closest_prior_approaches", "later_work",
    "research_directions_connected_to_limitations", "potentially_underexplored_areas",
    "evidence_scope",
}


def _f1(expected: set[str], predicted: set[str]) -> dict[str, float]:
    true_positive = len(expected & predicted)
    precision = true_positive / len(predicted) if predicted else 0.0
    recall = true_positive / len(expected) if expected else 1.0
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
    return {"precision": round(precision, 4), "recall": round(recall, 4), "f1": round(f1, 4)}


def _path_set(paths: list[Any]) -> set[tuple[str, ...]]:
    return {tuple(path) for path in paths if isinstance(path, list) and all(isinstance(item, str) for item in path)}


def _evidence_key(record: dict[str, Any]) -> tuple[str, str, str]:
    return (record.get("source_id", ""), record.get("target_id", ""), record.get("relationship_type", ""))


def _entity_ids(state: Any) -> set[str]:
    fields = ("paper_id", "problem_id", "method_id", "task_id", "benchmark_id", "limitation_id", "direction_id")
    return {getattr(entity, field) for collection in (state.papers, state.research_problems, state.methods, state.tasks, state.benchmarks, state.limitations, state.research_directions) for entity in collection for field in fields if hasattr(entity, field)}


def _score_evidence(state: Any, result: dict[str, Any], expected: list[dict[str, str]]) -> float:
    valid_state_keys = {_evidence_key(rel.model_dump(mode="json")) for rel in state.relationships}
    predicted = {
        _evidence_key(item) for item in result.get("evidence", [])
        if isinstance(item, dict) and item.get("evidence") and _evidence_key(item) in valid_state_keys
    }
    expected_keys = {_evidence_key(item) for item in expected}
    return round(len(predicted & expected_keys) / len(expected_keys), 4) if expected_keys else 1.0


def _unsupported_rate(state: Any, result: dict[str, Any]) -> float:
    entity_ids = _entity_ids(state)
    evidence_ids = {value for item in result.get("evidence", []) if isinstance(item, dict) for value in (item.get("source_id"), item.get("target_id"))}
    claims = [value for key in ("matched_research_problems", "related_methods", "related_papers", "known_limitations", "relevant_benchmarks", "research_directions") for value in result.get(key, [])]
    unsupported = sum(value not in entity_ids or value not in evidence_ids for value in claims)
    return round(unsupported / len(claims), 4) if claims else 0.0


def _schema_valid(result: Any) -> bool:
    return isinstance(result, dict) and RESULT_KEYS <= result.keys() and isinstance(result.get("evidence"), list) and isinstance(result.get("reasoning_paths"), list) and isinstance(result.get("confidence"), (int, float))


def evaluate(dataset: dict[str, Any], state: Any) -> dict[str, Any]:
    if dataset.get("dataset_type") != "new_proposal_holdout":
        raise ValueError("Evaluation data must declare dataset_type=new_proposal_holdout")
    proposals = dataset.get("proposals", [])
    construction_paper_ids = {paper.paper_id for paper in state.papers}
    reasoner = ProposalReasoner(state)
    rows = []
    examples = []
    for proposal in proposals:
        if proposal.get("proposal_id") in construction_paper_ids:
            raise ValueError(f"Evaluation proposal ID overlaps construction paper ID: {proposal['proposal_id']}")
        result = reasoner.reason(proposal["text"])
        gold = proposal["gold"]
        expected_paths = _path_set(gold["relationship_paths"])
        predicted_paths = _path_set([item.get("path", []) for item in result["reasoning_paths"] if isinstance(item, dict)])
        path_score = {"precision": 1.0, "recall": 1.0, "f1": 1.0} if not expected_paths and not predicted_paths else _f1(expected_paths, predicted_paths)
        row = {
            "proposal_id": proposal["proposal_id"],
            "prior_paper_identification": _f1(set(gold["prior_paper_ids"]), set(result["related_papers"])),
            "method_identification": _f1(set(gold["method_ids"]), set(result["related_methods"])),
            "research_problem_identification": _f1(set(gold["problem_ids"]), set(result["matched_research_problems"])),
            "relationship_traversal_correctness": path_score,
            "evidence_grounding": _score_evidence(state, result, gold["evidence"]),
            "unsupported_conclusion_rate": _unsupported_rate(state, result),
            "structured_output_validity": 1.0 if _schema_valid(result) else 0.0,
            "predicted": {"papers": result["related_papers"], "methods": result["related_methods"], "problems": result["matched_research_problems"], "paths": sorted(predicted_paths)},
        }
        rows.append(row)
        examples.append({"proposal_id": proposal["proposal_id"], "text": proposal["text"], "scores": row})

    metric_names = [key for key in rows[0] if key not in {"proposal_id", "predicted"}] if rows else []
    averages = {
        name: round(sum((row[name]["f1"] if isinstance(row[name], dict) else row[name]) for row in rows) / len(rows), 4)
        for name in metric_names
    } if rows else {}
    return {"dataset": dataset["dataset_name"], "construction_dataset": state.metadata.dataset_name, "proposal_count": len(proposals), "averages": averages, "per_proposal": rows, "representative_examples": examples}


def _write_markdown(report: dict[str, Any], path: Path) -> None:
    lines = ["# Research Proposal Evaluation", "", f"Dataset: `{report['dataset']}`", f"Holdout proposals: {report['proposal_count']}", "", "## Quantitative results", "", "| Metric | Mean |", "|---|---:|"]
    lines.extend(f"| {name.replace('_', ' ').title()} | {value:.4f} |" for name, value in report["averages"].items())
    lines.extend(["", "## Representative examples", ""])
    for example in report["representative_examples"]:
        lines.extend([f"### {example['proposal_id']}", example["text"], "", "```json", json.dumps(example["scores"], indent=2), "```", ""])
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Evaluate new proposals against a construction knowledge state.")
    parser.add_argument("--dataset", default="data/evaluation/proposals.json")
    parser.add_argument("--state", default="data/knowledge_state/knowledge_state.json")
    parser.add_argument("--output", default="data/evaluation/report.json")
    parser.add_argument("--markdown", default="data/evaluation/report.md")
    args = parser.parse_args()
    dataset = json.loads(Path(args.dataset).read_text(encoding="utf-8"))
    report = evaluate(dataset, load_knowledge_state(Path(args.state)))
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    _write_markdown(report, Path(args.markdown))
    print(json.dumps(report["averages"], indent=2))


if __name__ == "__main__":
    main()