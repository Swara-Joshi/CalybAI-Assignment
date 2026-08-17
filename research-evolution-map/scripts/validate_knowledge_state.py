from __future__ import annotations

import json
from pathlib import Path

from src.knowledge.serializer import load_knowledge_state
from src.knowledge.validator import validate_knowledge_state


def main() -> None:
    path = Path(__file__).resolve().parents[1] / "data" / "knowledge_state" / "knowledge_state.json"
    if not path.exists():
        print(f"Knowledge state file not found: {path}")
        return

    state = load_knowledge_state(path)
    errors = validate_knowledge_state(state)

    print(json.dumps({
        "paper_count": len(state.papers),
        "relationship_count": len(state.relationships),
        "validation_errors": errors,
        "metadata": state.metadata.model_dump(mode="json"),
    }, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
