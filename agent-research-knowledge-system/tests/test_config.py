from agent_research_knowledge_system.config import Settings


def test_settings_defaults() -> None:
    settings = Settings()

    assert settings.app_name == "agent-research-knowledge-system"
    assert settings.app_env == "development"
    assert settings.log_level == "INFO"
    assert settings.request_timeout_seconds == 30
