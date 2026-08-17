from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application configuration for the knowledge system."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = Field(default="agent-research-knowledge-system")
    app_env: str = Field(default="development")
    log_level: str = Field(default="INFO")

    research_data_dir: str = Field(default="./data")
    raw_data_dir: str = Field(default="./data/raw")
    processed_data_dir: str = Field(default="./data/processed")
    knowledge_state_dir: str = Field(default="./data/knowledge_state")

    request_timeout_seconds: int = Field(default=30)
    max_retries: int = Field(default=3)
    httpx_verify_ssl: bool = Field(default=True)

    @property
    def root_dir(self) -> Path:
        return Path(__file__).resolve().parents[2]

    @property
    def research_data_path(self) -> Path:
        return self.root_dir / self.research_data_dir


@lru_cache
def get_settings() -> Settings:
    return Settings()
