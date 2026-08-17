from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.knowledge.serializer import load_knowledge_state
from src.reasoning.reasoner import ProposalReasoner


def main() -> None:
    parser = argparse.ArgumentParser(description="Reason over a new research proposal using the serialized knowledge state.")
    parser.add_argument("--input", required=True, help="Natural-language research proposal to reason about.")
    parser.add_argument("--state", default="data/knowledge_state/knowledge_state.json", help="Path to the serialized knowledge state JSON file.")
    parser.add_argument("--format", choices=("json", "human"), default="json", help="Output format (default: json).")
    args = parser.parse_args()

    state = load_knowledge_state(Path(args.state))
    reasoner = ProposalReasoner(state)
    result = reasoner.reason(args.input)
    if args.format == "json":
        print(json.dumps(result, indent=2, ensure_ascii=False))
        return

    print(f"Proposal: {result['proposal_summary']}")
    print(f"Confidence: {result['confidence']} (dataset-grounded, not a novelty judgment)")
    print("\nClosest prior approaches:")
    for approach in result["closest_prior_approaches"]:
        print(f"- {approach['title']} ({approach['paper_id']}): {approach['why_relevant']}")
        print(f"  Problems: {', '.join(item['name'] for item in approach['problems_addressed']) or 'none recorded'}")
        print(f"  Methods: {', '.join(item['name'] for item in approach['methods_used']) or 'none recorded'}")
        print(f"  Limitations: {', '.join(item['name'] for item in approach['limitations_identified']) or 'none recorded'}")
        print(f"  Evidence records: {len(approach['evidence'])}")
    print("\nLater work:")
    for item in result["later_work"]:
        print(f"- {item['relationship']}: {item['title']} -> {item['on_paper_id']} ({item['evidence']['evidence']})")
    print("\nRelevant benchmarks: " + (", ".join(result["relevant_benchmarks"]) or "none recorded"))
    print("Research directions: " + (", ".join(result["research_directions"]) or "none recorded"))
    print("\nPotentially underexplored areas:")
    for item in result["potentially_underexplored_areas"]:
        print(f"- {item['qualification']} {item['area']}")


if __name__ == "__main__":
    main()
