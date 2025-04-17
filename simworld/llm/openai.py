import os
from typing import List, Dict, Any, Optional, Union
from openai import OpenAI

class OpenAI:
    def __init__(
        self,
        model: str,
        api_key: Optional[str] = None,
        api_base: Optional[str] = None,
        organization: Optional[str] = None,
    ):
        """
        Initialize the OpenAI wrapper.
        
        Args:
            model: The name of the OpenAI model to use.
            api_key: The API key for authentication. If not provided, will look for OPENAI_API_KEY environment variable.
            api_base: Base URL for the API. If not provided, will use the default OpenAI base URL.
            organization: The organization ID. If not provided, will look for OPENAI_ORGANIZATION environment variable.
        """
        self.model = model
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY")
        
        if not self.api_key:
            raise ValueError("API key must be provided either through the api_key parameter or OPENAI_API_KEY environment variable.")
        
        # Initialize the OpenAI client
        self.client = OpenAI(
            api_key=self.api_key,
            base_url=api_base,
        )
        
        # Check if the model is an instruction-following model
        # This can be expanded with a more comprehensive list of instruction models
        self.is_instruct_model = any(prefix in model.lower() for prefix in 
                                     ["gpt-3.5", "gpt-4", "text-davinci", "claude"])
    
    def generate(
        self,
        messages: List[Dict[str, str]],
        max_tokens: Optional[int] = None,
        temperature: float = 1.0,
        top_p: float = 1.0,
        num_return_sequences: int = 1,
        action_space: Any = None,
        **kwargs
    ) -> Union[str, List[str]]:
        """
        Generate responses from the OpenAI model.
        
        Args:
            messages: A list of message dictionaries with 'role' and 'content' keys.
            max_tokens: Maximum number of tokens to generate.
            temperature: Controls randomness. Higher values (e.g., 1.0) make output more random,
                         lower values (e.g., 0.2) make it more deterministic.
            top_p: Controls diversity via nucleus sampling. 1.0 means no nucleus sampling.
            num_return_sequences: How many completions to generate.
            action_space: Response format specification. If None, returns raw text.
            **kwargs: Additional arguments to pass to the OpenAI API.
            
        Returns:
            Generated text or list of generated texts.
        """
        # Handle the instruction model case
        if self.is_instruct_model:
            response = self.client.beta.chat.completions.parse(
                model=self.model,
                messages=messages,
                max_tokens=max_tokens,
                temperature=temperature,
                top_p=top_p,
                n=num_return_sequences,
                response_format=action_space,
                **kwargs,
            )
            
            return response.choices[0].message.content
        else:
            # For non-instruction models, use the completions API
            # This is a simplified version and may need to be adjusted
            prompt = "\n".join([f"{m['role']}: {m['content']}" for m in messages])
            response = self.client.completions.create(
                model=self.model,
                prompt=prompt,
                max_tokens=max_tokens,
                temperature=temperature,
                top_p=top_p,
                n=num_return_sequences,
                **kwargs,
            )
            
            if num_return_sequences == 1:
                return response.choices[0].text.strip()
            else:
                return [choice.text.strip() for choice in response.choices]
    
    def __call__(self, *args, **kwargs):
        """
        Allows the class instance to be called like a function.
        This simply calls the generate method.
        """
        return self.generate(*args, **kwargs)