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
    args = parser.parse_args()

    state = load_knowledge_state(Path(args.state))
    reasoner = ProposalReasoner(state)
    result = reasoner.reason(args.input)
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
