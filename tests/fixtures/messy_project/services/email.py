import logging

logger = logging.getLogger(__name__)


def send_email(to: str, subject: str) -> None:
    print(f"Sending email to {to}...")
    logger.info("Email sent to %s", to)
