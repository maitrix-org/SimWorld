from typing import List
import numpy as np
import json
import math
import random
from pathlib import Path
from simworld.utils.input_parser import InputParser
from simworld.utils.embedding_utils import get_single_image_embedding
from simworld.utils.retrive_utils import *
from simworld.citygen.dataclass import Building, Bounds, Point
from functools import lru_cache


# Use LLMs to parse the natural language input
def get_parsed_input(natural_language_input):
    api_key = "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"
    inputParser = InputParser(api_key)
    parsed_input = inputParser.parse_input(natural_language_input)
    asset_to_place = parsed_input["asset_to_place"]
    reference_asset_query = parsed_input["reference_asset"]
    relation = parsed_input["relation"]
    surroundings_query = parsed_input["surrounding_assets"]
    return parsed_input, asset_to_place, reference_asset_query, relation, surroundings_query


@lru_cache(maxsize=1)
def load_instance_desc_map():
    root_dir = Path(__file__).resolve().parents[2]
    desc_json_path = root_dir / "input" / "DescriptionMap.json"
    with open(desc_json_path , "r", encoding="utf-8") as f:
        return json.load(f)

# Integrate the surrounding information
def get_surroundings(data):
    details = []
    print(data)
    for asset, count in data["element_stats"].items():
        details.extend([asset] * count)
    buildings = list(data["building_stats"].keys())
    instance_desc_map = load_instance_desc_map()
    buildings_descriptions = [instance_desc_map.get(name, "") for name in buildings]
    candidate_surroundings_str = ", ".join(details + buildings_descriptions)
    return candidate_surroundings_str

# Compute the cosine similarity for embeddings
def cosine_similarity(vec1, vec2):
    dot = np.dot(vec1, vec2)
    norm1 = np.linalg.norm(vec1)
    norm2 = np.linalg.norm(vec2)
    if norm1 == 0 or norm2 == 0:
        return 0
    return dot / (norm1 * norm2)

# Construct Building type for best candidate
def construct_building_from_candidate(candidate: dict) -> Building:
    root_dir = Path(__file__).resolve().parents[2]
    buildings_json_path = root_dir / "output" / "buildings.json"
    with open(buildings_json_path, "r", encoding="utf-8") as f:
        buildings_data = json.load(f)
    
    candidate_type = candidate.get("instance_name", "")
    candidate_location = candidate.get("properties", {}).get("location", {})
    candidate_x = candidate_location.get("x", 0) / 100.0
    candidate_y = candidate_location.get("y", 0) / 100.0

    threshold: float = 1.0

    for b in buildings_data.get("buildings", []):
        if b.get("type", "") != candidate_type:
            continue
        center = b.get("center", {})
        center_x = center.get("x", 0)
        center_y = center.get("y", 0)
        distance = math.sqrt((center_x - candidate_x) ** 2 + (center_y - candidate_y) ** 2)
        if distance <= threshold:
            b_bounds = b.get("bounds", {})
            bounds = Bounds(
                x=b_bounds.get("x", 0),
                y=b_bounds.get("y", 0),
                width=b_bounds.get("width", 0),
                height=b_bounds.get("height", 0),
                rotation=b_bounds.get("rotation", 0)
            )
            return Building(building_type=candidate_type, bounds=bounds)
    
    print("No matching building found.")
    return None


def get_coordinates_around_building(conf, building: Building, relation: str, num_points: int = 1) -> List[Point]:
    r = math.radians(building.rotation)
    cx, cy = building.center.x, building.center.y

    offset = conf['citygen']['element']['element_building_distance']
    variation_ratio = 0.3
    random_variation = lambda: random.uniform(-variation_ratio, variation_ratio) * offset

    dirs = ["front", "back", "left", "right"]
    if relation.lower() not in dirs:
        relation = random.choice(dirs)

    if relation.lower() == "front":
        distance = building.height / 2 + offset
        dvec = (math.cos(r), math.sin(r))
        pvec = (-math.sin(r), math.cos(r)) 
        span = building.width
    elif relation.lower() == "back":
        distance = building.height / 2 + offset
        dvec = (-math.cos(r), -math.sin(r))
        pvec = (-math.sin(r), math.cos(r))
        span = building.width
    elif relation.lower() == "left":
        distance = building.width / 2 + offset
        dvec = (-math.sin(r), math.cos(r))
        pvec = (-math.cos(r), -math.sin(r))
        span = building.height
    elif relation.lower() == "right":
        distance = building.width / 2 + offset
        dvec = (math.sin(r), -math.cos(r))
        pvec = (math.cos(r), math.sin(r))
        span = building.height


    base_x = cx + distance * dvec[0]
    base_y = cy + distance * dvec[1]

    points = []
    if num_points == 1:
        x = base_x + random_variation()
        y = base_y + random_variation()
        points.append(Point(x, y))
    else:
        effective_span = span * 0.5
        for i in range(num_points):
            if num_points == 1:
                offset_along = 0
            else:
                offset_along = -effective_span / 2 + (effective_span * i / (num_points - 1))
            x = base_x + offset_along * pvec[0] + random_variation()
            y = base_y + offset_along * pvec[1] + random_variation()
            points.append(Point(x, y))
    return points


# Use CLIP to obtain the asset and place around the best candidate
def retrieve_target_asset(assets_description):
    root_dir = Path(__file__).resolve().parents[2]
    folder_path = root_dir / "input" / "sample_dataset"
    image_data_df = create_image_dataframe(folder_path)
    image_data_df["img_embeddings"] = image_data_df["image"].apply(get_single_image_embedding)
    related_assets = get_related_assets(assets_description, image_data_df)
    return related_assets

def place_target_asset(related_assets, positions):
    root_dir = Path(__file__).resolve().parents[2]
    json_output = generate_json(related_assets, positions)
    print(json_output)
    output_file = root_dir / "output" / "simple_world_asset.json"
    with open(output_file, "w") as f:
        f.write(json_output)
