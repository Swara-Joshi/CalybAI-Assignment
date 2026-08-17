from __future__ import annotations

from typing import Any

from src.knowledge.state import KnowledgeState


class EvidenceCollector:
    """Collect explicit evidence from relationships attached to the knowledge state."""

    def __init__(self, knowledge_state: KnowledgeState) -> None:
        self.knowledge_state = knowledge_state

    def collect(self, entity_ids: list[str]) -> list[dict[str, Any]]:
        evidence: list[dict[str, Any]] = []
        for rel in self.knowledge_state.relationships:
            if rel.source_id in entity_ids or rel.target_id in entity_ids:
                if hasattr(rel, "evidence"):
                    evidence.append(
                        {
                            "source_id": rel.source_id,
                            "target_id": rel.target_id,
                            "relationship_type": rel.relationship_type,
                            "evidence": rel.evidence,
                            "source_paper_id": rel.source_paper_id,
                            "confidence": rel.confidence,
                        }
                    )
        return evidence
