"""Base LLM class for handling interactions with language models."""

import json
import os
import re

import openai

from .retry import LLMResponseParsingError, retry_llm_call


class BaseLLM:
    """Base class for interacting with language models through OpenAI-compatible APIs."""

    def __init__(
        self,
        model_name,
        url,
        api_key=None,
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

    @retry_llm_call()
    def generate_text(
        self,
        system_prompt: str,
        user_prompt: str,
        max_tokens: int = 2048,
        temperature: float = 0.5,
        top_p: float = None,
    ) -> str:
        """Generate text using the language model.

        Args:
            system_prompt: System prompt to guide model behavior.
            user_prompt: User input prompt.
            max_tokens: Maximum number of tokens to generate.
            temperature: Sampling temperature.
            top_p: Top p sampling parameter.

        Returns:
            Generated text response.
        """
        response = self.client.chat.completions.create(
            model=self.model_name,
            messages=[
                {'role': 'system', 'content': system_prompt},
                {'role': 'user', 'content': user_prompt},
            ],
            max_tokens=max_tokens,
            temperature=temperature,
            top_p=top_p,
        )
        return response.choices[0].message.content

    @retry_llm_call()
    def generate_text_structured(
        self,
        system_prompt: str,
        user_prompt: str,
        output_format: str,
        few_shot_examples: str = '',
        max_tokens: int = 2048,
        temperature: float = 0.5,
        top_p: float = None,
    ) -> str:
        """Generate structured text output using a Pydantic model.

        Args:
            system_prompt: System prompt to guide model behavior.
            user_prompt: User input prompt.
            output_format: Expected JSON structure format.
            few_shot_examples: Examples to guide the model output.
            max_tokens: Maximum number of tokens to generate.
            temperature: Sampling temperature.
            top_p: Top p sampling parameter.

        Returns:
            JSON string matching the specified format.
        """
        format_message = (
            f'You must respond with a valid JSON object that matches the following structure: '
            f'{output_format}'
        )
        user_prompt = (
            f'{user_prompt}\n{format_message}\n{few_shot_examples}'
        )
        response = self.client.chat.completions.create(
            model=self.model_name,
            messages=[
                {'role': 'system', 'content': system_prompt},
                {'role': 'user', 'content': user_prompt},
            ],
            max_tokens=max_tokens,
            temperature=temperature,
            response_format={'type': 'json_object'},
            top_p=top_p,
        )
        try:
            content = response.choices[0].message.content
            try:
                parsed = json.loads(content)
                return json.dumps(parsed)
            except json.JSONDecodeError:
                if '```json' in content and '```' in content:
                    block = content.split('```json')[1].split('```')[0].strip()
                    try:
                        json.loads(block)
                        return block
                    except json.JSONDecodeError:
                        raise LLMResponseParsingError('Invalid JSON in markdown block')
                raise LLMResponseParsingError('No JSON or markdown JSON block found')
        except Exception as e:
            raise LLMResponseParsingError(f'Failed to parse LLM response: {e}')


if __name__ == '__main__':
    fmt = """
    {
        'actions': [0, 2, ...],
        'waypoints': ['Vector(x=1.0, y=2.0)', 'Vector(x=2.0, y=3.0)', ...],
    }
    """
    system_prompt = """
    You are a helpful assistant.
    """
    user_prompt = """
    You support action are:
    0: navigate
    1: pickup
    2: drop
    output as format
    """
    llm = BaseLLM(
        model_name='meta-llama/llama-3.3-70b-instruct',
        url='https://openrouter.ai/api/v1',
        api_key='sk-or-v1-...'
    )
    resp = llm.generate_text_structured(system_prompt, user_prompt, fmt)
    print(f'Response: {resp}')
    data = json.loads(resp)
    waypoints = []
    for point in data.get('waypoints', []):
        match = re.search(r'Vector\(x=([\-\d.]+), y=([\-\d.]+)\)', point)
        if match:
            waypoints.append((float(match.group(1)), float(match.group(2))))
    print(waypoints)
