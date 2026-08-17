import pytest
from pydantic import ValidationError

from agent_research_knowledge_system.config import ResearchScope, Settings


def test_settings_defaults() -> None:
    settings = Settings()

    assert settings.app_name == "agent-research-knowledge-system"
    assert settings.app_env == "development"
    assert settings.log_level == "INFO"
    assert settings.request_timeout_seconds == 30


def test_research_scope_defaults() -> None:
    scope = ResearchScope()

    assert scope.research_topic == "LLM agent research"
    assert scope.target_paper_count == 25
    assert scope.date_range.start.isoformat() == "2022-01-01"
    assert scope.date_range.end.isoformat() == "2025-12-31"
    assert scope.allowed_paper_sources == ["arxiv", "OpenAlex", "Semantic Scholar"]
    assert scope.search_queries
    assert scope.metadata_fields


def test_research_scope_validates_date_range() -> None:
    with pytest.raises(ValidationError, match="start.*end|end.*start"):
        ResearchScope(
            date_range={
                "start": "2025-06-01",
                "end": "2024-12-31",
            }
        )


def test_research_scope_rejects_empty_values() -> None:
    with pytest.raises(ValidationError):
        ResearchScope(research_topic="")

    with pytest.raises(ValidationError):
        ResearchScope(target_paper_count=0)

    with pytest.raises(ValidationError):
        ResearchScope(search_queries=[])

    with pytest.raises(ValidationError):
        ResearchScope(metadata_fields=[])
