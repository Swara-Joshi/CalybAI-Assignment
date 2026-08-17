from __future__ import annotations

import re
from typing import Any


class ProposalConcepts:
    """Explicit concepts extracted from a new research proposal."""

    def __init__(self, text: str) -> None:
        self.text = text.strip()
        self.tokens = self._tokenize(self.text)
        self.key_phrases = self._extract_key_phrases(self.tokens)
        self.concepts = self._normalize_concepts(self.key_phrases)

    def _tokenize(self, text: str) -> list[str]:
        return re.findall(r"[A-Za-z][A-Za-z0-9\- ]+", text.lower())

    def _extract_key_phrases(self, tokens: list[str]) -> list[str]:
        phrases: list[str] = []
        for phrase in ["persistent memory", "tool interactions", "llm agent", "planning", "memory", "tool use", "multi agent coordination"]:
            if phrase in " ".join(tokens):
                phrases.append(phrase)
        return phrases or [token for token in tokens if len(token) > 3][:10]

    def _normalize_concepts(self, phrases: list[str]) -> list[str]:
        normalized: list[str] = []
        for phrase in phrases:
            cleaned = re.sub(r"\s+", " ", phrase.strip())
            if cleaned and cleaned not in normalized:
                normalized.append(cleaned)
        return normalized


def parse_proposal(text: str) -> ProposalConcepts:
    return ProposalConcepts(text)
