from __future__ import annotations

from datetime import date

from pydantic import BaseModel, Field, field_validator, model_validator


class ResearchConfig(BaseModel):
    """Explicit research scope configuration for the LLM agent research study."""

    topic: str = Field(default="Evolution of LLM Agent Research")
    subtopics: list[str] = Field(
        default_factory=lambda: [
            "planning",
            "tool use",
            "memory",
            "multi agent coordination",
        ]
    )
    target_paper_count: int = Field(default=75, ge=1)
    min_paper_count: int = Field(default=50, ge=1)
    max_paper_count: int = Field(default=100, ge=1)
    sources: list[str] = Field(
        default_factory=lambda: ["arXiv", "OpenAlex", "Semantic Scholar"]
    )
    queries: list[str] = Field(
        default_factory=lambda: [
            "LLM agent planning research",
            "LLM tool use agent research",
            "LLM agent memory research",
            "multi-agent coordination LLM research",
        ]
    )
    date_range: dict[str, date] = Field(
        default_factory=lambda: {
            "start": date(2022, 1, 1),
            "end": date(2025, 12, 31),
        }
    )

    @field_validator("topic")
    @classmethod
    def validate_topic(cls, value: str) -> str:
        if not value or not value.strip():
            raise ValueError("topic must not be empty")
        return value.strip()

    @field_validator("subtopics")
    @classmethod
    def validate_subtopics(cls, value: list[str]) -> list[str]:
        if not value:
            raise ValueError("subtopics must not be empty")
        cleaned = [item.strip() for item in value if item and item.strip()]
        if not cleaned:
            raise ValueError("subtopics must contain at least one non-empty value")
        return cleaned

    @field_validator("sources")
    @classmethod
    def validate_sources(cls, value: list[str]) -> list[str]:
        if not value:
            raise ValueError("sources must not be empty")
        cleaned = [item.strip() for item in value if item and item.strip()]
        if not cleaned:
            raise ValueError("sources must contain at least one non-empty value")
        return cleaned

    @field_validator("queries")
    @classmethod
    def validate_queries(cls, value: list[str]) -> list[str]:
        if not value:
            raise ValueError("queries must not be empty")
        cleaned = [item.strip() for item in value if item and item.strip()]
        if not cleaned:
            raise ValueError("queries must contain at least one non-empty value")
        return cleaned

    @field_validator("target_paper_count")
    @classmethod
    def validate_target_count(cls, value: int) -> int:
        if value < 1:
            raise ValueError("target_paper_count must be at least 1")
        return value

    @field_validator("min_paper_count", "max_paper_count")
    @classmethod
    def validate_range_bounds(cls, value: int) -> int:
        if value < 1:
            raise ValueError("paper counts must be at least 1")
        return value

    @field_validator("date_range")
    @classmethod
    def validate_date_range(cls, value: dict[str, date]) -> dict[str, date]:
        start = value.get("start")
        end = value.get("end")
        if start is None or end is None:
            raise ValueError("date_range must include both start and end dates")
        if start > end:
            raise ValueError("date_range.start must be before or equal to date_range.end")
        return value

    @model_validator(mode="after")
    def validate_paper_count_range(self) -> "ResearchConfig":
        if self.min_paper_count > self.max_paper_count:
            raise ValueError("min_paper_count must be less than or equal to max_paper_count")
        if not self.min_paper_count <= self.target_paper_count <= self.max_paper_count:
            raise ValueError(
                "target_paper_count must be between min_paper_count and max_paper_count"
            )
        return self

    @property
    def target_range(self) -> tuple[int, int]:
        return (self.min_paper_count, self.max_paper_count)

    @property
    def is_target_within_range(self) -> bool:
        return self.min_paper_count <= self.target_paper_count <= self.max_paper_count
