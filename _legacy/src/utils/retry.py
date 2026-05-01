from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
    before_sleep_log,
)
from loguru import logger
import logging

# Bridge loguru into standard logging for tenacity
_std_logger = logging.getLogger("tenacity")


def make_retry(max_attempts: int = 3, min_wait: int = 2, max_wait: int = 30):
    """
    Factory: returns a @retry decorator with exponential backoff.

    Usage:
        @make_retry(max_attempts=3)
        async def call_jira():
            ...
    """
    return retry(
        stop=stop_after_attempt(max_attempts),
        wait=wait_exponential(multiplier=2, min=min_wait, max=max_wait),
        retry=retry_if_exception_type(Exception),
        before_sleep=before_sleep_log(_std_logger, logging.WARNING),
        reraise=True,
    )
