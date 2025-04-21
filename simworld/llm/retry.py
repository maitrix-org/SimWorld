"""Retry decorator module for handling LLM API call retries with exponential backoff."""

import functools
import logging
import time

import openai

logger = logging.getLogger(__name__)


class LLMResponseParsingError(Exception):
    """Raised when LLM response parsing fails."""
    pass


def retry_api_call(
    max_retries: int = 5,
    initial_delay: float = 1.0,
    exponential_base: float = 2.0,
    rate_limit_per_min: int = 20,
):
    """Decorator for retrying LLM API calls with exponential backoff.

    Handles API-related errors like network issues, timeouts, and rate limits.

    Args:
        max_retries: Maximum number of retry attempts before giving up.
        initial_delay: Initial delay between retries in seconds.
        exponential_base: Base for exponential backoff calculation.
        rate_limit_per_min: Maximum number of calls allowed per minute.

    Returns:
        Decorated function that implements API retry logic.
    """
    api_exceptions = (
        openai.APIError,
        openai.APIConnectionError,
        openai.APITimeoutError,
        openai.RateLimitError,
    )

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
                except api_exceptions as e:
                    last_exception = e
                    if attempt == max_retries:
                        logger.error(f'API call failed after {max_retries} retries. Last error: {str(e)}')
                        raise

                    wait_time = delay * (exponential_base ** attempt)
                    logger.warning(
                        f'API attempt {attempt + 1}/{max_retries} failed: {str(e)}. '
                        f'Retrying in {wait_time:.2f} seconds...'
                    )
                    time.sleep(wait_time)

            raise last_exception
        return wrapper
    return decorator


def retry_parsing(
    max_retries: int = 3,
    initial_delay: float = 0.1,
    exponential_base: float = 2.0,
):
    """Decorator for retrying LLM response parsing with exponential backoff.

    Handles parsing errors that might occur when processing LLM responses.

    Args:
        max_retries: Maximum number of retry attempts before giving up.
        initial_delay: Initial delay between retries in seconds.
        exponential_base: Base for exponential backoff calculation.

    Returns:
        Decorated function that implements parsing retry logic.
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            delay = initial_delay
            last_exception = None

            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except LLMResponseParsingError as e:
                    last_exception = e
                    if attempt == max_retries:
                        logger.error(f'Parsing failed after {max_retries} retries. Last error: {str(e)}')
                        raise

                    wait_time = delay * (exponential_base ** attempt)
                    logger.warning(
                        f'Parsing attempt {attempt + 1}/{max_retries} failed: {str(e)}. '
                        f'Retrying in {wait_time:.2f} seconds...'
                    )
                    time.sleep(wait_time)

            raise last_exception
        return wrapper
    return decorator
