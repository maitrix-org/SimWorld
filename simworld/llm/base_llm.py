"""Base LLM class for handling interactions with language models."""

import inspect
import os
import time
from typing import Optional

import openai

from .retry import retry_api_call


class LLMMetaclass(type):
    """Metaclass to automatically add retry decorators to public methods."""
    def __new__(cls, name, bases, attrs):
        """Create a new class."""
        # Process all attributes that are functions
        for attr_name, attr_value in attrs.items():
            # Only process public methods (not starting with _)
            if not attr_name.startswith('_') and inspect.isfunction(attr_value):
                # Apply retry decorator to the method
                attrs[attr_name] = retry_api_call()(attr_value)

        return super().__new__(cls, name, bases, attrs)


class BaseLLM(metaclass=LLMMetaclass):
    """Base class for interacting with language models through OpenAI-compatible APIs."""

    def __init__(
        self,
        model_name: str,
        url: Optional[str] = 'https://api.openai.com/v1',
        api_key: Optional[str] = None,
    ):
        """Initialize the LLM client.

        Args:
            model_name: Name of the model to use.
            url: Base URL for the API.
            api_key: Optional API key (will use OPENAI_API_KEY env var if not provided).
        """
        env_api_key = os.getenv('OPENAI_API_KEY')
        if env_api_key is None and api_key is None:
            raise ValueError('No API key provided')
        self.client = openai.OpenAI(
            api_key=env_api_key if env_api_key else api_key,
            base_url=url,
        )
        self.model_name = model_name

    def generate_text(
        self,
        system_prompt: str,
        user_prompt: str,
        max_tokens: int = 2048,
        temperature: float = 0.5,
        top_p: float = None,
        **kwargs,
    ) -> str | None:
        """Generate text using the language model.

        Args:
            system_prompt: System prompt to guide model behavior.
            user_prompt: User input prompt.
            max_tokens: Maximum number of tokens to generate.
            temperature: Sampling temperature.
            top_p: Top p sampling parameter.

        Returns:
            Generated text response or None if generation fails.
        """
        start_time = time.time()
        try:
            response = self._generate_text_with_retry(
                system_prompt,
                user_prompt,
                max_tokens,
                temperature,
                top_p,
                **kwargs,
            )
            return response, time.time() - start_time
        except Exception:
            return None, time.time() - start_time

    def _generate_text_with_retry(
        self,
        system_prompt: str,
        user_prompt: str,
        max_tokens: int = 2048,
        temperature: float = 0.5,
        top_p: float = None,
        **kwargs,
    ) -> str:
        response = self.client.chat.completions.create(
            model=self.model_name,
            messages=[
                {'role': 'system', 'content': system_prompt},
                {'role': 'user', 'content': user_prompt},
            ],
            max_tokens=max_tokens,
            temperature=temperature,
            top_p=top_p,
            **kwargs,
        )
        return response.choices[0].message.content
