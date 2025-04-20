"""Retry decorator module for handling LLM API call retries with exponential backoff."""

import functools
import logging
import time
from typing import Type, Union

import openai

logger = logging.getLogger(__name__)


class LLMResponseParsingError(Exception):
    """Raised when LLM response parsing fails."""
    pass


def retry_llm_call(
    max_retries: int = 5,
    initial_delay: float = 1.0,
    exponential_base: float = 2.0,
    rate_limit_per_min: int = 20,
    exceptions: Union[Type[Exception], tuple[Type[Exception], ...]] = (
        openai.APIError,
        openai.APIConnectionError,
        openai.APITimeoutError,
        openai.RateLimitError,
        LLMResponseParsingError,
    ),
):
    """Decorator for retrying LLM API calls with exponential backoff.

    Args:
        max_retries: Maximum number of retry attempts before giving up.
        initial_delay: Initial delay between retries in seconds.
        exponential_base: Base for exponential backoff calculation.
        rate_limit_per_min: Maximum number of calls allowed per minute.
        exceptions: Exception types that should trigger a retry.

    Returns:
        Decorated function that implements retry logic.
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            delay = initial_delay
            last_exception = None

            for attempt in range(max_retries + 1):
                if rate_limit_per_min is not None:
                    time.sleep(60 / rate_limit_per_min)
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    if attempt == max_retries:
                        logger.error(f'Failed after {max_retries} retries. Last error: {str(e)}')
                        raise

                    wait_time = delay * (exponential_base ** attempt)
                    logger.warning(
                        f'Attempt {attempt + 1}/{max_retries} failed: {str(e)}. '
                        f'Retrying in {wait_time:.2f} seconds...'
                    )
                    time.sleep(wait_time)

            raise last_exception
        return wrapper
    return decorator
