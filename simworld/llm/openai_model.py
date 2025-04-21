"""OpenAI model implementation for LLM interactions."""
import base64
import io
from typing import Optional, Union

import cv2
import numpy as np
from PIL import Image

from simworld.llm.base_llm import BaseLLM


class OpenAIModel(BaseLLM):
    """OpenAI model implementation for LLM interactions."""

    def __init__(self, model_name: str, url: str = None, api_key: str = None, additional_prompt: str = 'ANSWER', **kwargs):
        """Initialize the OpenAI model.

        Args:
            model_name: Model name to use
            url: Optional API URL override
            api_key: Optional API key override
            additional_prompt: Additional prompt to append to user messages
            **kwargs: Additional arguments to pass to the base model
        """
        super().__init__(model_name, url, api_key, **kwargs)
        self.additional_prompt = additional_prompt
        self.is_instruct_model = False
        self.model = model_name

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
        stop: Optional[str] = None,
        logprobs: Optional[int] = None,
        temperature=None,
        additional_prompt=None,
        action_history: Optional[list[str]] = None,
        is_instruct_model: bool = False,
        **kwargs,
    ):
        """Generate function calls using the OpenAI model."""
        max_tokens = kwargs.get('max_tokens', self.max_tokens if hasattr(self, 'max_tokens') else None)
        temperature = kwargs.get('temperature', self.temperature if hasattr(self, 'temperature') else None)

        messages = [{'role': 'system', 'content': system_prompt}]

        is_instruct_model = self._check_if_instruct_model()
        supports_vision = self._check_if_supports_vision()

        if images and not supports_vision:
            raise ValueError(f'Model {self.model} does not support vision/multimodal inputs')

        user_content = self._build_user_content(user_prompt, images, action_history, supports_vision)
        messages.append({'role': 'user', 'content': user_content if len(user_content) > 1 else user_content[0]['text']})

        if is_instruct_model:
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
            return self._process_function_response(response)
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

    def generate(
        self,
        system_prompt: Optional[Union[str, list[str]]],
        user_prompt: Optional[Union[str, list[str]]],
        images: Optional[Union[str, list[str], np.ndarray, list[np.ndarray]]] = None,
        max_tokens: int = None,
        top_p: float = 1.0,
        num_return_sequences: int = 1,
        logprobs: Optional[int] = None,
        temperature=None,
        additional_prompt=None,
        action_history: Optional[list[str]] = None,
        is_instruct_model: bool = False,
        **kwargs,
    ):
        """Generate text using the OpenAI model."""
        max_tokens = kwargs.get('max_tokens', self.max_tokens if hasattr(self, 'max_tokens') else None)
        temperature = kwargs.get('temperature', self.temperature if hasattr(self, 'temperature') else None)

        supports_vision = self._check_if_supports_vision()
        messages = [{'role': 'system', 'content': system_prompt}]

        user_content = self._build_user_content(user_prompt, images, action_history, supports_vision)
        messages.append({'role': 'user', 'content': user_content if len(user_content) > 1 else user_content[0]['text']})

        is_instruct_model = self._check_if_instruct_model()

        if is_instruct_model:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                max_tokens=max_tokens,
                temperature=temperature,
                top_p=top_p,
                n=num_return_sequences,
                **kwargs,
            )
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

    def react(
        self,
        system_prompt: str,
        context_prompt: str,
        user_prompt: str,
        reasoning_prompt: str,
        images: Optional[Union[str, list[str], np.ndarray, list[np.ndarray]]] = None,
        max_tokens: int = None,
        temperature: float = None,
        top_p: float = 1.0,
        **kwargs
    ):
        """ReAct-1: Reasoning and Acting."""
        reasoning_prompt = reasoning_prompt.format(context=context_prompt)

        # First, make a reasoning
        reasoning_response = self.client.chat.completions.create(
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

        # Then, make a user prompt
        user_prompt = user_prompt.format(context=context_prompt, reasoning=reasoning)

        # Finally, make a response
        response = self.client.chat.completions.create(
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

    def _check_if_instruct_model(self) -> bool:
        """Check if the current model is an instruct model."""
        if self.is_instruct_model:
            return True

        model_name = self.model.lower()
        return any(name in model_name for name in ['gpt-3.5', 'gpt-4', 'instruct'])

    def _check_if_supports_vision(self) -> bool:
        """Check if the current model supports vision/multimodal inputs."""
        multimodal_models = ['gpt-4o', 'gpt-4o-mini', 'o1', 'o1-mini']
        return self.model.lower() in multimodal_models

    def _build_user_content(
        self,
        user_prompt: Optional[Union[str, list[str]]],
        images: Optional[Union[str, list[str], np.ndarray, list[np.ndarray]]],
        action_history: Optional[list[str]],
        supports_vision: bool
    ) -> list:
        """Build the user content list for the message."""
        user_content = []

        if user_prompt:
            user_content.append({'type': 'text', 'text': user_prompt})

        if images and supports_vision:
            if isinstance(images, str):
                images = [images]
            for image in images:
                img_data = image if isinstance(image, str) else self._process_image_to_base64(image)
                user_content.append({
                    'type': 'image_url',
                    'image_url': {'url': f'data:image/jpeg;base64,{img_data}'}
                })

        if action_history:
            user_content.append({'type': 'text', 'text': f'Your action history is: {action_history}'})

        return user_content

    def _process_function_response(self, response):
        """Process the function call response."""
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


if __name__ == '__main__':
    llm = OpenAIModel(model_name='gpt-4o-mini', api_key='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')
    response = llm.generate('You are a helpful assistant.', 'What is the capital of France?')
    print(response)
