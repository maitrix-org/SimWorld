"""
Base class for all LLM models.
"""
from typing import Optional, Union
import numpy as np
from openai import OpenAI
import time
import os


class BaseModel:
    """
    Base class for all LLM models.
    """
    def __init__(self, url: Optional[str] = None, api_key: Optional[str] = None, model: str = "meta-llama/Meta-Llama-3.1-70B-Instruct"):
        self.url = url
        self.api_key = api_key
        if self.api_key is None:
            self.api_key = os.getenv("OPENAI_API_KEY")
        if self.url is None:
            self.url = "https://api.openai.com/v1"
        self.client = OpenAI(base_url=self.url, api_key=self.api_key)
        self.model = model
        self.max_tokens = 1000
        self.temperature = 0.7
        self.top_p = 1.0
        self.num_return_sequences = 1
        self.rate_limit_per_min = 20
        self.logprobs = None

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
        """
        Generate text from the model.
        """
        max_tokens = self.max_tokens if max_tokens is None else max_tokens
        temperature = self.temperature if temperature is None else temperature
        logprobs = 0 if logprobs is None else logprobs

        supports_vision = False
        multimodal_models = ["gpt-4o", "gpt-4o-mini", "o1", "o1-mini"]
        model_name = self.model.lower()
        if model_name in multimodal_models:
            supports_vision = True

        messages = [{"role": "system", "content": system_prompt}]
        user_content = []
        if user_prompt:
            user_content.append({"type": "text", "text": user_prompt})
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
                    "type": "image_url",
                    "image_url": {"url": f"data:image/jpeg;base64,{img_data}"}
                })

        if action_history:
            user_content.append({"type": "text", "text": f"Your action history is: {action_history}"})

        messages.append({"role": "user", "content": user_content if len(user_content) > 1 else user_content[0]["text"]})

        for i in range(1, retry + 1):
            try:
                # sleep several seconds to avoid rate limit
                if rate_limit_per_min is not None:
                    time.sleep(60 / rate_limit_per_min)
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    max_tokens=max_tokens,
                    temperature=temperature,
                    top_p=top_p,
                    n=num_return_sequences,
                    **kwargs,
                )
                return response.choices[0].message.content
            except Exception as e:
                print(f"An Error Occured: {e}, sleeping for {i} seconds")
                time.sleep(i)

        # after 64 tries, still no luck
        raise RuntimeError(
            "GPTCompletionModel failed to generate output, even after 64 tries"
        )

if __name__ == "__main__":
    llm = BaseModel(url="https://openrouter.ai/api/v1",
                    api_key="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",
                    model="meta-llama/llama-4-maverick"
                    )

    response = llm.generate("You are a helpful assistant.", "What is the capital of France?")
    print(response)
