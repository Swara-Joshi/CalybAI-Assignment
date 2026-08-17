from __future__ import annotations

from agent_research_knowledge_system.config import get_settings
from agent_research_knowledge_system.logging_config import configure_logging


def main() -> None:
    settings = get_settings()
    logger = configure_logging(settings.log_level)
    logger.info("Starting %s in %s mode", settings.app_name, settings.app_env)


if __name__ == "__main__":
    main()
