from typing import Optional, Union
import numpy as np
from openai import OpenAI
from simworld.llm.base_model import BaseModel
import time
from simworld.utils.exact_json import extract_json_and_fix_escapes
import os

class OpenRouterModel(BaseModel):
    def __init__(self, url: Optional[str] = None, api_key: Optional[str] = None, model: str = "meta-llama/Meta-Llama-3.1-70B-Instruct"):
        super().__init__(url, api_key, model)
        self.model = model
        self.max_tokens = 1000
        self.temperature = 0.7
        self.top_p = 1.0
        self.num_return_sequences = 1
        self.rate_limit_per_min = 20
        self.logprobs = None
        if self.api_key is None:
            self.api_key = os.getenv("OPENROUTER_API_KEY")
        self.client = OpenAI(base_url=self.url, api_key=self.api_key)

    def react(self, system_prompt: str,
                context_prompt: str,
                user_prompt: str,
                reasoning_prompt: str,
                images: Optional[Union[str, list[str], np.ndarray, list[np.ndarray]]] = None,
                max_tokens: int = None,
                top_p: float = 1.0,
                num_return_sequences: int = 1,
                rate_limit_per_min: Optional[int] = 20,
                logprobs: Optional[int] = None,
                reasoning_space_schema: Optional[str] = None,
                action_space_schema: Optional[str] = None,
                temperature=None,
                additional_prompt=None,
                retry=4,
                action_history: Optional[list[str]] = None,
                is_instruct_model: bool = False,
                **kwargs):
        """
            ReAct-1: Reasoning and Acting
            The model will first make a reasoning according to the prompt, then consider the function calling if there is necessary.
            Then the model will act according to the reasoning and function calling.
        """
        max_tokens = self.max_tokens if max_tokens is None else max_tokens
        temperature = self.temperature if temperature is None else temperature
        num_return_sequences = self.num_return_sequences if num_return_sequences is None else num_return_sequences

        # 1. 添加超时设置
        kwargs['timeout'] = kwargs.get('timeout', 30)  # 设置30秒超时

        # 2. 修改推理提示，确保模型知道需要返回JSON格式
        reasoning_prompt = reasoning_prompt.format(context=context_prompt)
        reasoning_prompt += "\nPlease respond in valid JSON format following this schema: " + str(reasoning_space_schema)

        # print("reasoning_prompt: ", reasoning_prompt)

        reasoning_response = None
        for i in range(1, retry + 1):
            try:
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": reasoning_prompt}
                    ],
                    max_tokens=max_tokens,
                    temperature=temperature,
                    top_p=top_p,
                    **kwargs,
                )
                # print("response:", response)
                reasoning_response = response.choices[0].message.content
                break
            except Exception as e:
                print(f"Reasoning Error Occurred: {e}, attempt {i}/{retry}")
                if i < retry:
                    time.sleep(min(i * 2, 10))
                continue

        if reasoning_response is None:
            print("Warning: Failed to get reasoning response, using default")
            reasoning_json = {"reasoning": "No reasoning available"}
        else:
            reasoning_json = extract_json_and_fix_escapes(reasoning_response)
            if reasoning_json is None:
                reasoning_json = {"reasoning": "No reasoning available"}

        reasoning = reasoning_json.get("reasoning", "No reasoning available")

        # 4. 修改动作提示，确保模型知道需要返回JSON格式
        user_prompt = user_prompt.format(
            context=context_prompt,
            reasoning=reasoning.reasoning
        )
        user_prompt += "\nPlease respond in valid JSON format following this schema: " + str(action_space_schema)

        # print("user_prompt: ", user_prompt)

        action_response = None
        for i in range(1, retry + 1):
            try:
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    max_tokens=max_tokens,
                    temperature=temperature,
                    top_p=top_p,
                    **kwargs,
                )
                action_response = response.choices[0].message.content
                break
            except Exception as e:
                print(f"Action Error Occurred: {e}, attempt {i}/{retry}")
                if i < retry:
                    time.sleep(min(i * 2, 10))
                continue

        if action_response is None:
            print("Warning: Failed to get action response, using default")
            action_json = {
                "choice": 0,
                "index": 0,
                "target_point": [0, 0],
                "meeting_point": [0, 0],
                "next_waypoint": [0, 0],
                "new_speed": 0,
            }
        else:
            action_json = extract_json_and_fix_escapes(action_response)
            if action_json is None:
                action_json = {
                    "choice": 0,
                    "index": 0,
                    "target_point": [0, 0],
                    "meeting_point": [0, 0],
                    "next_waypoint": [0, 0],
                    "new_speed": 0,
                }

        return action_json

if __name__ == "__main__":
    llm = OpenRouterModel(url="https://openrouter.ai/api/v1",
                    api_key="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",
                    model="meta-llama/llama-4-maverick"
                    )

    response = llm.generate("You are a helpful assistant.", "What is the capital of France?")
    print(response)
