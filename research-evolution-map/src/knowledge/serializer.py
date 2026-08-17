from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from src.knowledge.state import KnowledgeState
from src.knowledge.validator import validate_knowledge_state


class KnowledgeStateSerializer:
    """Serialize and deserialize a knowledge state to JSON."""

    def __init__(self, output_path: str | Path | None = None) -> None:
        self.output_path = Path(output_path) if output_path else Path("data/knowledge_state/knowledge_state.json")

    def save(self, state: KnowledgeState, *, validate: bool = True) -> Path:
        if validate:
            errors = validate_knowledge_state(state)
            if errors:
                raise ValueError("Knowledge state validation failed: " + "; ".join(errors))

        self.output_path.parent.mkdir(parents=True, exist_ok=True)
        payload = state.model_dump(mode="json")
        self.output_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
        return self.output_path

    def load(self) -> KnowledgeState:
        payload = json.loads(self.output_path.read_text(encoding="utf-8"))
        state = KnowledgeState.model_validate(payload)
        errors = validate_knowledge_state(state)
        if errors:
            raise ValueError("Knowledge state validation failed after loading: " + "; ".join(errors))
        return state


def save_knowledge_state(state: KnowledgeState, output_path: str | Path | None = None) -> Path:
    serializer = KnowledgeStateSerializer(output_path)
    return serializer.save(state)


def load_knowledge_state(path: str | Path) -> KnowledgeState:
    serializer = KnowledgeStateSerializer(path)
    return serializer.load()
