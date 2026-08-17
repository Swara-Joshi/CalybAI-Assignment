import pytest
from pydantic import ValidationError

from src.config.settings import ResearchConfig


def test_research_config_defaults() -> None:
    config = ResearchConfig()

    assert config.topic == "Evolution of LLM Agent Research"
    assert config.subtopics == [
        "planning",
        "tool use",
        "memory",
        "multi agent coordination",
    ]
    assert config.target_paper_count == 75
    assert config.min_paper_count == 50
    assert config.max_paper_count == 100
    assert config.sources == ["arXiv", "OpenAlex", "Semantic Scholar"]
    assert len(config.queries) >= 1
    assert config.date_range["start"].isoformat() == "2022-01-01"
    assert config.date_range["end"].isoformat() == "2025-12-31"
    assert config.is_target_within_range is True


def test_research_config_validates_value_ranges() -> None:
    with pytest.raises(ValidationError):
        ResearchConfig(target_paper_count=0)

    with pytest.raises(ValidationError):
        ResearchConfig(min_paper_count=0)

    with pytest.raises(ValidationError):
        ResearchConfig(max_paper_count=0)


def test_research_config_validates_scope_bounds() -> None:
    with pytest.raises(ValidationError):
        ResearchConfig(target_paper_count=10, min_paper_count=50, max_paper_count=100)

    with pytest.raises(ValidationError):
        ResearchConfig(date_range={"start": "2025-01-01", "end": "2024-01-01"})


def test_research_config_rejects_empty_values() -> None:
    with pytest.raises(ValidationError):
        ResearchConfig(topic="")

    with pytest.raises(ValidationError):
        ResearchConfig(subtopics=[])

    with pytest.raises(ValidationError):
        ResearchConfig(sources=[])

    with pytest.raises(ValidationError):
        ResearchConfig(queries=[])
