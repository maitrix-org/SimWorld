"""OpenAI model implementation for LLM interactions."""
import base64
import io
import json
import os
import time
from typing import Optional, Union

import cv2
import numpy as np
from openai import OpenAI
from PIL import Image

from simworld.llm.base_model import BaseModel


class OpenAIModel(BaseModel):
    """OpenAI model implementation for LLM interactions."""

    def __init__(self, url: Optional[str] = None, api_key: Optional[str] = None, model: str = 'gpt-4o-mini', additional_prompt: str = 'ANSWER', **kwargs):
        """Initialize the OpenAI model.

        Args:
            url: Optional API URL override
            api_key: Optional API key override
            model: Model name to use
            additional_prompt: Additional prompt to append to user messages
            **kwargs: Additional arguments to pass to the base model
        """
        self.url = url
        self.api_key = api_key
        self.model = model
        super().__init__(url, api_key, model, **kwargs)
        self.additional_prompt = additional_prompt
        self.is_instruct_model = False
        if self.api_key is None:
            self.api_key = os.getenv('OPENAI_API_KEY')
        if self.url is None:
            self.client = OpenAI(api_key=self.api_key)
        else:
            self.client = OpenAI(base_url=self.url, api_key=self.api_key)

    def _process_image_to_base64(self, image: np.ndarray) -> str:
        """Convert numpy array image to base64 string.

        Args:
            image: Image array (1 or 3 channels)

        Returns:
            Base64 encoded image string
        """
        # Convert single channel to 3 channels if needed
        if len(image.shape) == 2 or (len(image.shape) == 3 and image.shape[2] == 1):
            image = cv2.cvtColor(image, cv2.COLOR_GRAY2RGB)

        # Ensure uint8 type
        if image.dtype != np.uint8:
            image = (image * 255).astype(np.uint8)

        # Convert to PIL Image
        pil_image = Image.fromarray(image)

        # Convert to base64
        buffered = io.BytesIO()
        pil_image.save(buffered, format='JPEG')
        img_str = base64.b64encode(buffered.getvalue()).decode()

        return img_str

    def function_calling(
        self,
        system_prompt: Optional[Union[str, list[str]]],
        user_prompt: Optional[Union[str, list[str]]],
        images: Optional[Union[str, list[str], np.ndarray, list[np.ndarray]]] = None,
        functions: Optional[dict] = None,
        max_tokens: int = None,
        top_p: float = 1.0,
        num_return_sequences: int = 1,
        rate_limit_per_min: Optional[int] = 20,
        stop: Optional[str] = None,
        logprobs: Optional[int] = None,
        temperature=None,
        additional_prompt=None,
        retry=64,
        action_history: Optional[list[str]] = None,
        is_instruct_model: bool = False,
        **kwargs,
    ):
        """Generate function calls using the OpenAI model.

        Args:
            system_prompt: System prompt to guide model behavior
            user_prompt: User prompt to generate response for
            images: Optional images to include in the prompt
            functions: Optional function definitions
            max_tokens: Maximum number of tokens to generate
            top_p: Nucleus sampling parameter
            num_return_sequences: Number of sequences to return
            rate_limit_per_min: Rate limit in requests per minute
            stop: Stop sequence for generation
            logprobs: Number of log probabilities to return
            temperature: Sampling temperature
            additional_prompt: Additional prompt to append
            retry: Number of retry attempts
            action_history: Optional action history
            is_instruct_model: Whether this is an instruct model
            **kwargs: Additional arguments

        Returns:
            List of function call results
        """
        max_tokens = self.max_tokens if max_tokens is None else max_tokens
        temperature = self.temperature if temperature is None else temperature
        logprobs = 0 if logprobs is None else logprobs

        messages = [{'role': 'system', 'content': system_prompt}]

        is_instruct_model = self.is_instruct_model
        if not is_instruct_model:
            # Recheck if the model is an instruct model with model name
            model_name = self.model.lower()
            if (
                ('gpt-3.5' in model_name)
                or ('gpt-4' in model_name)
                or ('instruct' in model_name)
            ):
                is_instruct_model = True

        # check if the model supports vision/multimodal inputs
        supports_vision = False
        multimodal_models = ['gpt-4o', 'gpt-4o-mini', 'o1', 'o1-mini']
        model_name = self.model.lower()
        if model_name in multimodal_models:
            supports_vision = True

        if images and not supports_vision:
            raise ValueError(f'Model {self.model} does not support vision/multimodal inputs')

        for i in range(1, retry + 1):
            try:
                if rate_limit_per_min is not None:
                    time.sleep(60 / rate_limit_per_min)

                if is_instruct_model:
                    user_content = []
                    if action_history:
                        user_content.append({'type': 'text', 'text': f'Your action history is: {action_history}'})
                    # build the message content
                    if user_prompt:
                        user_content.append({'type': 'text', 'text': user_prompt})
                    if images and supports_vision:
                        if isinstance(images, str):
                            images = [images]
                        for image in images:
                            # If image is already a base64 string, use it directly
                            if isinstance(image, str):
                                img_data = image
                            else:
                                img_data = self._process_image_to_base64(image)
                            user_content.append({
                                'type': 'image_url',
                                'image_url': {'url': f'data:image/jpeg;base64,{img_data}'}
                            })

                    messages.append({'role': 'user', 'content': user_content if len(user_content) > 1 else user_content[0]['text']})

                    with open('messages.json', 'w') as f:
                        json.dump(messages, f)

                    response = self.client.chat.completions.create(
                        model=self.model,
                        messages=messages,
                        max_tokens=max_tokens,
                        temperature=temperature,
                        top_p=top_p,
                        n=num_return_sequences,
                        tools=functions if functions else [],
                        tool_choice='required'
                    )
                    # process the returned results
                    results = []
                    for choice in response.choices:
                        if hasattr(choice, 'function') and choice.function:
                            results.append({
                                'function_call': {
                                    'name': choice.function.name,
                                    'arguments': choice.function.arguments
                                }
                            })
                        else:
                            results.append(choice.message.tool_calls)

                    return results
                else:
                    response = self.client.chat.completions.create(
                        model=self.model,
                        messages=messages,
                        max_tokens=max_tokens,
                        temperature=temperature,
                        top_p=top_p,
                        n=num_return_sequences,
                        logprobs=0,
                        **kwargs,
                    )
                    return response.choices[0].message.content

            except Exception as e:
                print(f'An Error Occurred: {e}, sleeping for {i} seconds')
                time.sleep(i)

        raise RuntimeError(
            'GPTCompletionModel failed to generate output, even after 64 tries'
        )

    def generate(
        self,
        system_prompt: Optional[Union[str, list[str]]],
        user_prompt: Optional[Union[str, list[str]]],
        images: Optional[Union[str, list[str], np.ndarray, list[np.ndarray]]] = None,
        max_tokens: int = None,
        top_p: float = 1.0,
        num_return_sequences: int = 1,
        rate_limit_per_min: Optional[int] = 20,
        logprobs: Optional[int] = None,
        temperature=None,
        additional_prompt=None,
        retry=64,
        action_history: Optional[list[str]] = None,
        is_instruct_model: bool = False,
        **kwargs,
    ):
        """Generate text using the OpenAI model.

        Args:
            system_prompt: System prompt to guide model behavior
            user_prompt: User prompt to generate response for
            images: Optional images to include in the prompt
            max_tokens: Maximum number of tokens to generate
            top_p: Nucleus sampling parameter
            num_return_sequences: Number of sequences to return
            rate_limit_per_min: Rate limit in requests per minute
            logprobs: Number of log probabilities to return
            temperature: Sampling temperature
            additional_prompt: Additional prompt to append
            retry: Number of retry attempts
            action_history: Optional action history
            is_instruct_model: Whether this is an instruct model
            **kwargs: Additional arguments

        Returns:
            Generated text response
        """
        max_tokens = self.max_tokens if max_tokens is None else max_tokens
        temperature = self.temperature if temperature is None else temperature
        logprobs = 0 if logprobs is None else logprobs

        supports_vision = False
        multimodal_models = ['gpt-4o', 'gpt-4o-mini', 'o1', 'o1-mini']
        model_name = self.model.lower()
        if model_name in multimodal_models:
            supports_vision = True

        messages = [{'role': 'system', 'content': system_prompt}]
        user_content = []
        if user_prompt:
            user_content.append({'type': 'text', 'text': user_prompt})
        if images and supports_vision:
            if isinstance(images, str):
                images = [images]
            for image in images:
                # If image is already a base64 string, use it directly
                if isinstance(image, str):
                    img_data = image
                else:
                    img_data = self._process_image_to_base64(image)
                user_content.append({
                    'type': 'image_url',
                    'image_url': {'url': f'data:image/jpeg;base64,{img_data}'}
                })

        if action_history:
            user_content.append({'type': 'text', 'text': f'Your action history is: {action_history}'})

        messages.append({'role': 'user', 'content': user_content if len(user_content) > 1 else user_content[0]['text']})

        is_instruct_model = self.is_instruct_model
        if not is_instruct_model:
            # Recheck if the model is an instruct model with model name
            model_name = self.model.lower()
            if (
                ('gpt-3.5' in model_name)
                or ('gpt-4' in model_name)
                or ('instruct' in model_name)
            ):
                is_instruct_model = True

        for i in range(1, retry + 1):
            try:
                # sleep several seconds to avoid rate limit
                if rate_limit_per_min is not None:
                    time.sleep(60 / rate_limit_per_min)
                # GPT 3.5 and higher use a different API
                if is_instruct_model:
                    response = self.client.beta.chat.completions.parse(
                        model=self.model,
                        messages=messages,
                        max_tokens=max_tokens,
                        temperature=temperature,
                        top_p=top_p,
                        n=num_return_sequences,
                        **kwargs,
                    )
                    return response.choices[0].message.content
                else:
                    response = self.client.chat.completions.create(
                        model=self.model,
                        messages=messages,
                        max_tokens=max_tokens,
                        temperature=temperature,
                        top_p=top_p,
                        n=num_return_sequences,
                        logprobs=0,
                        **kwargs,
                    )
                    return response.choices[0].message.content

            except Exception as e:
                print(f'An Error Occured: {e}, sleeping for {i} seconds')
                time.sleep(i)

        # after 64 tries, still no luck
        raise RuntimeError(
            'GPTCompletionModel failed to generate output, even after 64 tries'
        )

    def react(self, system_prompt: str,
              context_prompt: str,
              user_prompt: str,
              reasoning_prompt: str,
              images: Optional[Union[str, list[str], np.ndarray, list[np.ndarray]]] = None,
              max_tokens: int = None,
              temperature: float = None,
              top_p: float = 1.0,
              **kwargs):
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
            top_p: Nucleus sampling parameter
            **kwargs: Additional arguments

        Returns:
            Generated response
        """
        reasoning_prompt = reasoning_prompt.format(context=context_prompt)
        # first, make a reasoning
        reasoning_response = self.client.beta.chat.completions.parse(
            model=self.model,
            messages=[
                {'role': 'system', 'content': system_prompt},
                {'role': 'user', 'content': reasoning_prompt}
            ],
            max_tokens=max_tokens,
            temperature=temperature,
            top_p=top_p,
        )
        reasoning = reasoning_response.choices[0].message.content

        # then, make a user prompt
        user_prompt = user_prompt.format(context=context_prompt, reasoning=reasoning)

        # then, make a response
        response = self.client.beta.chat.completions.parse(
            model=self.model,
            messages=[
                {'role': 'system', 'content': system_prompt},
                {'role': 'user', 'content': user_prompt}
            ],
            max_tokens=max_tokens,
            temperature=temperature,
            top_p=top_p,
        )
        return response.choices[0].message.content


if __name__ == '__main__':
    llm = OpenAIModel(model='gpt-4o-mini')
    response = llm.generate('You are a helpful assistant.', 'What is the capital of France?')
    print(response)
