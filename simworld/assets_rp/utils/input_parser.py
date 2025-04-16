"""The module is prompting LLM to parse the input about asset retrieval and placement."""
import json

from openai import OpenAI

from simworld.assets_rp.prompt.retrieval_input_prompt import \
    scene_extraction_system_prompt


class InputParser:
    """The class will parse the input and return 4 parts: asset_to_place, reference_asset_query, relation, surroundings_query."""
    def __init__(self, api_key: str, model: str = 'gpt-3.5-turbo'):
        """Initialize the api_key and model of the class.

        Args:
            api_key: user's openai api key
            model: the name of the model
        """
        self.api_key = api_key
        self.model = model
        self.client = OpenAI(api_key=self.api_key)

    def parse_input(self, prompt: str) -> dict:
        """Call OpenAI API and parse the natural language input, it will extract 4 parts: asset_to_place, reference_asset, relation, surrounding_assets.

        Args:
            prompt: the text prompt provided by the user.

        Returns:
            asset_to_place: [ ... ], list that includes the assets we want to place
            reference_asset: "...", the reference asset
            surrounding_assets: "...", the surrounding assets user provide
        """
        try:
            system_message = scene_extraction_system_prompt
            user_message = f'Extract the scene details from the following prompt:\n\n{prompt}'

            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {'role': 'system', 'content': system_message},
                    {'role': 'user', 'content': user_message},
                ],
                temperature=0
            )
            message_content = response.choices[0].message.content.strip()

            print('LLM Response:', message_content)

            result = json.loads(message_content)

            if not (
                isinstance(result, dict)
                and 'asset_to_place' in result
                and 'reference_asset' in result
                and 'relation' in result
                and 'surrounding_assets' in result
            ):
                raise ValueError('Response does not contain required keys.')

            if not isinstance(result['asset_to_place'], list) or not all(isinstance(item, str) for item in result['asset_to_place']):
                raise ValueError('asset_to_place must be a list of strings.')
            if not isinstance(result['reference_asset'], str):
                raise ValueError('reference_asset must be a string.')
            if not isinstance(result['relation'], str):
                raise ValueError('relation must be a string.')
            if not isinstance(result['surrounding_assets'], str):
                raise ValueError('surrounding_assets must be a string.')

            return result

        except Exception as e:
            print(f'Error while parsing input: {e}')
            return {
                'asset_to_place': [],
                'reference_asset': '',
                'relation': '',
                'surrounding_assets': ''
            }
