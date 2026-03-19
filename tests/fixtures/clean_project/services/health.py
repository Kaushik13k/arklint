import logging

logger = logging.getLogger(__name__)


def check_health() -> dict:
    logger.info("Health check")
    return {"status": "ok"}
