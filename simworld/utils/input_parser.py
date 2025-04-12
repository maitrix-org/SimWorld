import json
from openai import OpenAI

class InputParser:
    def __init__(self, api_key: str, model: str = "gpt-3.5-turbo"):
        self.api_key = api_key
        self.model = model
        self.client = OpenAI(api_key = self.api_key)

    def parse_input(self, prompt: str) -> dict:
        """
        Call OpenAI API and parse the natural language input, it will extract the following three parts:
          - asset_to_place: the assets need to place (a string list)
          - reference_asset: the asset used as a reference (a string; a word)
          - surrounding_assets: the surrounding assets (a string; a complete sentence)
        
        Return format:
        {
            "asset_to_place": [ ... ],
            "reference_asset": "...",
            "surrounding_assets": "..."
        }
        """
        try:
            system_message = (
                "You are an assistant that extracts scene details for a world simulator. "
                "From a given natural language description, you need to extract exactly four keys: "
                "1. 'asset_to_place': a JSON array of strings representing the assets that need to be placed. "
                "2. 'reference_asset': a string representing the asset used as a reference (with words to describe it). "
                "3. 'relation': a single word only chosen from 4 elements: ['front', 'back', 'left', 'right'], which refers to the relation of the asset and the building."
                "4. 'surrounding_assets': a string (one sentence) describing the keywords of the surrounding environment. "
                "Your response must be a valid JSON object with these four keys and no additional text."
                "For example, if you get the input \" Put two bikes in front of this big, white school. I see a fountain, a hospital, and a apartment besides me. \""
                "Your response should be like : {\"asset_to_place\": [ \"bike\", \"bike\" ], \"reference_asset\": \"big, white school\", \"relation\": \"front\", \"surrounding_assets\": \"I see a fountain, a hospital, and a apartment besides me.\" } "
            )
            user_message = f"Extract the scene details from the following prompt:\n\n{prompt}"
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_message},
                    {"role": "user", "content": user_message},
                ],
                temperature=0
            )
            message_content = response.choices[0].message.content.strip()

            print("LLM Response:", message_content)
            
            result = json.loads(message_content)
            
            if not (
                isinstance(result, dict)
                and "asset_to_place" in result
                and "reference_asset" in result
                and "relation" in result
                and "surrounding_assets" in result
            ):
                raise ValueError("Response does not contain required keys.")
            
            if not isinstance(result["asset_to_place"], list) or not all(isinstance(item, str) for item in result["asset_to_place"]):
                raise ValueError("asset_to_place must be a list of strings.")
            if not isinstance(result["reference_asset"], str):
                raise ValueError("reference_asset must be a string.")
            if not isinstance(result["relation"], str):
                raise ValueError("relation must be a string.")
            if not isinstance(result["surrounding_assets"], str):
                raise ValueError("surrounding_assets must be a string.")
                
            return result
        
        except Exception as e:
            print(f"Error while parsing input: {e}")
            return {
                "asset_to_place": [],
                "reference_asset": "",
                "relation": "",
                "surrounding_assets": ""
            }
