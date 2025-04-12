import json
from openai import OpenAI

class ChatGPTKeywordExtractor:
    def __init__(self, api_key: str, model: str = "gpt-3.5-turbo"):
        self.api_key = api_key
        self.model = model
        self.client = OpenAI(api_key = self.api_key)

    def extract_keywords(self, prompt: str) -> list:

        try:
            system_message = (
                "You are a helpful assistant that extracts only keywords from user prompts. "
                "I'm asking you to extract the name of the assets I want to add to the scene."
                "You should include all the words describing assets with the keywords."
                "Please only respond with a JSON array of strings containing the keywords (e.g. [\"fridge\", \"blue box\"], [\"trash bin without covering\"] )."
            )
            user_message = f"Extract keywords from the following prompt:\n\n{prompt}"

            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_message},
                    {"role": "user", "content": user_message},
                ],
                temperature=0,
            )
            message_content = response.choices[0].message.content
            print(message_content)
            keywords = json.loads(message_content)

            if isinstance(keywords, list) and all(isinstance(k, str) for k in keywords):
                return keywords
            else:
                raise ValueError("Response is not a valid JSON array of strings.")

        except Exception as e:
            print(f"Error while extracting keywords: {e}")
            return []