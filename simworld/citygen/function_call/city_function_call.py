from simworld.citygen.city.city_generator import CityGenerator
from simworld.utils.data_exporter import DataExporter
from simworld.citygen.dataclass import Point, Segment
from typing import List
from simworld.config import Config
import os
import json
from typing import List
# from simworld.citygen.function_call.asset_retrieval.services.reference_assets_retrieval import ReferenceAssetsRetriever
from sentence_transformers import SentenceTransformer
# from simworld.citygen.function_call.asset_retrieval.adding_asset_tools import *

from simworld.utils.asset_rp_utils import *
from simworld.utils.reference_assets_retriever import ReferenceAssetsRetriever

class CityFunctionCall:
    """Function call for city"""

    def __init__(self, config: Config):
        """Initialize function call"""
        self.city_generator = CityGenerator(config)
        self.model = SentenceTransformer('paraphrase-MiniLM-L6-v2')

    def generate_city(self):
        """Generate city randomly with roads, buildings and elements"""
        self.city_generator.generate()

    def export_city(self, output_path: str):
        """Export city"""
        exporter = DataExporter(self.city_generator)
        exporter.export_to_json(output_path)

    def add_road(self, start: List[float], end: List[float]) -> int:
        """Add road"""
        StartPoint = Point(start[0], start[1])
        EndPoint = Point(end[0], end[1])
        self.city_generator.road_manager.add_segment(Segment(StartPoint, EndPoint))
        return len(self.city_generator.road_manager.roads) - 1

    def remove_road(self, id: int) -> bool:
        """Remove road"""
        try:
            segment = self.city_generator.road_manager.get_segment_by_id(id)
            self.city_generator.road_manager.remove_segment(segment)
            return True
        except IndexError:
            return False

    def modify_road(self, id: int, start: List[float], end: List[float]) -> bool:
        """Modify road"""
        try:
            segment = self.city_generator.road_manager.get_segment_by_id(id)
            old_segment = Segment(segment.start, segment.end)
            segment.start = Point(start[0], start[1])
            segment.end = Point(end[0], end[1])
            self.city_generator.road_manager.update_segment(old_segment, segment)
            return True
        except IndexError:
            return False

    def generate_road_network(self, num_segments: int):
        """Generate road network"""
        self.city_generator.road_generator.generate_initial_segments()
        while len(self.city_generator.road_manager.roads) < num_segments:
            self.city_generator.road_generator.generate_step()
        self.city_generator.road_generator.find_intersections()

    def generate_building_alone_road(self, road_id: int):
        """Generate building alone road"""
        segment = self.city_generator.road_manager.get_segment_by_id(road_id)
        self.city_generator.building_generator.generate_buildings_along_segment(segment, self.city_generator.road_manager.road_quadtree)

    def generate_building_alone_roads(self):
        """Generate building alone roads"""
        for road in self.city_generator.road_manager.roads:
            self.city_generator.building_generator.generate_buildings_along_segment(road, self.city_generator.road_manager.road_quadtree)

    def generate_element_alone_road(self, road_id: int):
        """Generate element alone road"""
        segment = self.city_generator.road_manager.get_segment_by_id(road_id)
        elements = self.city_generator.element_generator._add_elements_spline_road(segment)
        for element in elements:
            if self.city_generator.element_manager.can_place_element(element.bounds):
                self.city_generator.element_manager.add_element(element)

    def generate_element_alone_roads(self):
        """Generate element alone roads"""
        for road in self.city_generator.road_manager.roads:
            elements = self.city_generator.element_generator._add_elements_spline_road(road)
            for element in elements:
                if self.city_generator.element_manager.can_place_element(element.bounds):
                    self.city_generator.element_manager.add_element(element)

    def generate_element_around_buildings(self):
        """Generate element around buildings"""
        for building in self.city_generator.building_manager.buildings:
            elements = self.city_generator.element_generator._add_elements_around_building(building)
            for element in elements:
                if self.city_generator.element_manager.can_place_element(element.bounds):
                    self.city_generator.element_manager.add_element(element)
        self.city_generator.element_generator.filter_elements_by_buildings(self.city_generator.building_quadtree)

    def generate_assets_manually(self, natural_language_input):
        # Use LLMs to parse the natural language input
        parsed_input, asset_to_place, reference_asset_query, relation, surroundings_query = get_parsed_input(natural_language_input)

        print("LLM parse result:", parsed_input)

        # 2. Load the file that store all the assets. Find the candidates that match "reference_asset_query"
        root_dir = Path(__file__).resolve().parents[3]
        progen_world_path = root_dir / "output" / "progen_world.json"
        referenceAssetRetriever = ReferenceAssetsRetriever(progen_world_path)
        candidate_nodes = referenceAssetRetriever.retrieve_reference_assets(reference_asset_query)

        # 3. For each candidate, use "_get_point_around_label" to obtain its surrounding asset
        candidate_similarity_scores = []
        for candidate, base_score in candidate_nodes:
            x = candidate["properties"]["location"]["x"] / 100
            y = candidate["properties"]["location"]["y"] / 100
            node_position = Point(x, y)
            candidate_surroundings = self.city_generator.route_generator.get_point_around_label(node_position, self.city_generator.city_quadtrees, 200, 20)
            
            # 4. Integrate the surrounding information to a string and do embedding, and calculate the similarity score.
            candidate_surroundings_str = get_surroundings(candidate_surroundings)
            print(candidate_surroundings_str)
            candidate_embedding = self.model.encode(candidate_surroundings_str)
            query_embedding = self.model.encode(surroundings_query)
            
            similarity = cosine_similarity(candidate_embedding, query_embedding)
            candidate_similarity_scores.append((candidate, similarity))
            print(f"candidate nodes: {candidate['id']} similarity score: {similarity:.4f}")

        # 5. Choose the highest score as final reference asset and construct the instance
        best_candidate, best_similarity = max(candidate_similarity_scores, key=lambda x: x[1])
        print("best candidate:", best_candidate["id"], "similarity score:", best_similarity)
        reference_asset = construct_building_from_candidate(best_candidate)

        # 6. Use CLIP to obtain the asset and place around the best candidate
        target_assets = retrieve_target_asset(asset_to_place)
        target_positions = get_coordinates_around_building(self.city_generator.config, reference_asset, relation, len(target_assets))
        place_target_asset(target_assets, target_positions)
