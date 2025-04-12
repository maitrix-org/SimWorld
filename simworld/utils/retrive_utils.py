import os
import json
import random
import pandas as pd
from PIL import Image
from sklearn.metrics.pairwise import cosine_similarity
from simworld.utils.embedding_utils import get_single_text_embedding, get_single_image_embedding


def get_local_images(folder_path: str) -> list:
    image_paths = []
    for root, _, files in os.walk(folder_path):
        for file in files:
            if file.lower().endswith(('png', 'jpg', 'jpeg', 'bmp', 'gif', 'tiff')):
                image_paths.append(os.path.join(root, file))
    return image_paths

def load_image(image_path: str):
    try:
        image = Image.open(image_path)
        if image.mode == "P" and "transparency" in image.info:
            image = image.convert("RGBA")
        else:
            image = image.convert("RGB")
        return image
    except:
        return None

def create_image_dataframe(folder_path: str) -> pd.DataFrame:
    image_paths = get_local_images(folder_path)
    data = {
        "image_path": image_paths,
        "image": [load_image(path) for path in image_paths]
    }
    df = pd.DataFrame(data)
    df = df[df["image"].notnull()]
    return df

def generate_random_properties(x, y):
    return {
        "location": {
            "x": x,
            "y": y,
            "z": 0
        },
        "orientation": {
            "pitch": 0,
            "yaw": round(random.uniform(0, 360), 2),
            "roll": 0
        },
        "scale": {
            "x": round(random.uniform(0.8, 1.2), 2),
            "y": round(random.uniform(0.8, 1.2), 2),
            "z": 1.0
        }
    }

def generate_json(assets, positions):
    data = {"nodes": []}

    for idx, asset in enumerate(assets):
        node = {
            "id": f"BP_GEN_{asset}_{idx}",
            "instance_name": asset + "_C",
            "properties": generate_random_properties(positions[idx].x, positions[idx].y)
        }
        data["nodes"].append(node)

    return json.dumps(data, indent=2)


def get_top_assets(keyword: str, image_data_df: pd.DataFrame, top_K: int = 1) -> list:
    query_vect = get_single_text_embedding(keyword)
    image_data_df["cos_sim"] = image_data_df["img_embeddings"].apply(lambda x: cosine_similarity(query_vect, x)[0][0])
    top_results = image_data_df.sort_values(by="cos_sim", ascending=False)[0:top_K+1].head(top_K)
    return [os.path.splitext(os.path.basename(path))[0] for path in top_results["image_path"].tolist()]

def get_related_assets(keywords: list, image_data_df: pd.DataFrame, top_K: int = 1) -> list:
    return sum([get_top_assets(keyword, image_data_df, top_K) for keyword in keywords], [])

