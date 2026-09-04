import logging

from app.core.config import get_settings
from app.core.logging import configure_logging


def main() -> None:
    settings = get_settings()
    configure_logging(settings.log_level)
    logging.getLogger(__name__).info("No Phase 1 seed data is required")


if __name__ == "__main__":
    main()
