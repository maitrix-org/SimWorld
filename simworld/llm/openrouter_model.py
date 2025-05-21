"""OpenRouter model implementation for LLM interactions."""
from typing import Optional, Union

import numpy as np

from simworld.llm.base_llm import BaseLLM
from simworld.utils.extract_json import extract_json_and_fix_escapes


class OpenRouterModel(BaseLLM):
    """OpenRouter model implementation for LLM interactions."""

    def __init__(self, model_name: str, url: str = 'https://openrouter.ai/api/v1', api_key: str = None, **kwargs):
        """Initialize the OpenRouter model.

        Args:
            model_name: Model name to use
            url: Optional API URL override
            api_key: Optional API key override
            **kwargs: Additional arguments to pass to the base model
        """
        super().__init__(model_name, url, api_key, **kwargs)
        self.model = model_name
        # Default parameters
        self.max_tokens = kwargs.get('max_tokens', 1000)
        self.temperature = kwargs.get('temperature', 0.7)
        self.top_p = kwargs.get('top_p', 1.0)
        self.num_return_sequences = kwargs.get('num_return_sequences', 1)

    def react(
        self,
        system_prompt: str,
        context_prompt: str,
        user_prompt: str,
        reasoning_prompt: str,
        images: Optional[Union[str, list[str], np.ndarray, list[np.ndarray]]] = None,
        max_tokens: int = None,
        temperature: float = None,
        top_p: float = None,
        reasoning_space_schema: Optional[str] = None,
        action_space_schema: Optional[str] = None,
        default_reasoning_response: Optional[dict] = None,
        default_action_response: Optional[dict] = None,
        **kwargs
    ):
        """ReAct-1: Reasoning and Acting.

        The model will first make a reasoning according to the prompt, then consider the function calling if there is necessary.
        Then the model will act according to the reasoning and function calling.

        Args:
            system_prompt: System prompt to guide model behavior
            context_prompt: Context for the reasoning
            user_prompt: User prompt for the action
            reasoning_prompt: Prompt for the reasoning step
            images: Optional images to include
            max_tokens: Maximum number of tokens to generate
            temperature: Sampling temperature
            top_p: Top p sampling parameter
            reasoning_space_schema: JSON schema for reasoning response
            action_space_schema: JSON schema for action response
            **kwargs: Additional arguments

        Returns:
            Action JSON response
        """
        # Set default parameters
        max_tokens = kwargs.get('max_tokens', self.max_tokens)
        temperature = kwargs.get('temperature', self.temperature)
        top_p = kwargs.get('top_p', self.top_p)

        # Add timeout setting
        kwargs['timeout'] = kwargs.get('timeout', 30)

        # Get reasoning response
        reasoning_prompt = self._build_reasoning_prompt(reasoning_prompt, context_prompt, reasoning_space_schema)
        reasoning_response = self._get_completion(
            system_prompt=system_prompt,
            user_prompt=reasoning_prompt,
            max_tokens=max_tokens,
            temperature=temperature,
            top_p=top_p,
            **kwargs
        )

        reasoning_json = self._parse_json_response(
            reasoning_response,
            default=default_reasoning_response
        )
        reasoning = reasoning_json.get('reasoning', default_reasoning_response)

        # Get action response
        action_prompt = self._build_action_prompt(user_prompt, context_prompt, reasoning, action_space_schema)
        action_response = self._get_completion(
            system_prompt=system_prompt,
            user_prompt=action_prompt,
            max_tokens=max_tokens,
            temperature=temperature,
            top_p=top_p,
            **kwargs
        )

        return self._parse_json_response(action_response, default=default_action_response)

    def _get_completion(
        self,
        system_prompt: str,
        user_prompt: str,
        max_tokens: int,
        temperature: float,
        top_p: float,
        **kwargs
    ) -> str:
        """Get completion from the model.

        Args:
            system_prompt: System prompt
            user_prompt: User prompt
            max_tokens: Maximum tokens
            temperature: Temperature
            top_p: Top p
            **kwargs: Additional arguments

        Returns:
            Model response content
        """
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {'role': 'system', 'content': system_prompt},
                {'role': 'user', 'content': user_prompt}
            ],
            max_tokens=max_tokens,
            temperature=temperature,
            top_p=top_p,
            **kwargs,
        )
        return response.choices[0].message.content

    def _build_reasoning_prompt(
        self,
        reasoning_prompt: str,
        context_prompt: str,
        reasoning_space_schema: Optional[str]
    ) -> str:
        """Build the reasoning prompt.

        Args:
            reasoning_prompt: Base reasoning prompt
            context_prompt: Context information
            reasoning_space_schema: JSON schema for reasoning

        Returns:
            Complete reasoning prompt
        """
        prompt = reasoning_prompt.format(context=context_prompt)
        if reasoning_space_schema:
            prompt += '\nPlease respond in valid JSON format following this schema: ' + str(reasoning_space_schema)
        return prompt

    def _build_action_prompt(
        self,
        user_prompt: str,
        context_prompt: str,
        reasoning: str,
        action_space_schema: Optional[str]
    ) -> str:
        """Build the action prompt.

        Args:
            user_prompt: Base user prompt
            context_prompt: Context information
            reasoning: Reasoning from previous step
            action_space_schema: JSON schema for action

        Returns:
            Complete action prompt
        """
        prompt = user_prompt.format(
            context=context_prompt,
            reasoning=reasoning
        )
        if action_space_schema:
            prompt += '\nPlease respond in valid JSON format following this schema: ' + str(action_space_schema)
        return prompt

    def _parse_json_response(self, response: str, default: dict) -> dict:
        """Parse JSON response with fallback to default.

        Args:
            response: Response string to parse
            default: Default value if parsing fails

        Returns:
            Parsed JSON or default value
        """
        if response is None:
            return default

        result = extract_json_and_fix_escapes(response)
        return result if result is not None else default
