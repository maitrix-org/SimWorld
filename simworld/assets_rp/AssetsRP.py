"""This module provides functionality for retrieving and placing assets in the city simulation."""
import os

from sentence_transformers import SentenceTransformer

from simworld.assets_rp.utils.assets_rp_utils import (
    construct_building_from_candidate, get_coordinates_around_building,
    get_parsed_input, get_surroundings, place_target_asset,
    retrieve_target_asset, vector_cosine_similarity)
from simworld.assets_rp.utils.reference_assets_retriever import \
    ReferenceAssetsRetriever
from simworld.citygen.dataclass import Point
from simworld.config import Config
from simworld.utils.data_importer import DataImporter


class AssetsRetrieverPlacer:
    """Assets Retrieval and Placement ability.

    This class provides methods to retrieve the assets and place them somewhere
    based on the natural language prompts.
    """

    def __init__(self, config: Config):
        """Initialize function call.

        Args:
            config: the configuration user provide.
        """
        self.config = config
        self.model = SentenceTransformer(config['assets_rp.env_description_retrieval_model'])
        self.data_importer = DataImporter(config)
        self.city_generator = self.data_importer.import_city_data()

    def generate_assets_manually(self, natural_language_input, output_dir: str = None):
        """This function is used to retrieve and place the assets based on user's prompt.

        Args:
            natural_language_input: the text prompt provided by the users.
            output_dir: the directory to save the output.
        """
        # 1. Parse the input
        parsed_input, asset_to_place, reference_asset_query, relation, surroundings_query = get_parsed_input(natural_language_input, self.config['assets_rp.openai_api_key'])

        print('LLM parse result:', parsed_input)

        # 2. Load the file that store all the assets. Find the candidates that match "reference_asset_query"
        progen_world_path = os.path.join(self.config['citygen.output_dir'], 'progen_world.json')
        referenceAssetRetriever = ReferenceAssetsRetriever(progen_world_path, self.config['assets_rp.input_description_map'], self.config['assets_rp.env_description_retrieval_model'])
        candidate_nodes = referenceAssetRetriever.retrieve_reference_assets(reference_asset_query)

        # 3. For each candidate, use "_get_point_around_label" to obtain its surrounding asset
        candidate_similarity_scores = []
        for candidate, base_score in candidate_nodes:
            x = candidate['properties']['location']['x'] / 100
            y = candidate['properties']['location']['y'] / 100
            node_position = Point(x, y)
            candidate_surroundings = self.city_generator.route_generator.get_point_around_label(node_position, self.city_generator.city_quadtrees, 200, 20)

            # 4. Integrate the surrounding information to a string and do embedding, and calculate the similarity score.
            candidate_surroundings_str = get_surroundings(candidate_surroundings, self.config['assets_rp.input_description_map'])
            print(candidate_surroundings_str)
            candidate_embedding = self.model.encode(candidate_surroundings_str)
            query_embedding = self.model.encode(surroundings_query)

            similarity = vector_cosine_similarity(candidate_embedding, query_embedding)
            candidate_similarity_scores.append((candidate, similarity))
            print(f"candidate nodes: {candidate['id']} similarity score: {similarity:.4f}")

        # 5. Choose the highest score as final reference asset and construct the instance
        best_candidate, best_similarity = max(candidate_similarity_scores, key=lambda x: x[1])
        print('best candidate:', best_candidate['id'], 'similarity score:', best_similarity)
        reference_asset = construct_building_from_candidate(best_candidate, self.config['assets_rp.input_dir'])

        # 6. Use CLIP to obtain the asset and place around the best candidate
        target_assets = retrieve_target_asset(asset_to_place, self.config['assets_rp.input_sample_dataset'], self.config['assets_rp.assets_retrieval_model'])
        target_positions = get_coordinates_around_building(self.city_generator.config, reference_asset, relation, len(target_assets))
        place_target_asset(target_assets, target_positions, output_dir or self.config['assets_rp.output_dir'])
