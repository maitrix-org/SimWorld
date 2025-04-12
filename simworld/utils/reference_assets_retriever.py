import json
import faiss
from pathlib import Path
from sentence_transformers import SentenceTransformer

class ReferenceAssetsRetriever:
    def __init__(self, progen_world_path: str):
        self.progen_world_path = progen_world_path
        self.model = SentenceTransformer('paraphrase-MiniLM-L6-v2')
        self.nodes = self._load_nodes()
        root_dir = Path(__file__).resolve().parents[2]
        desc_json_path = root_dir / "input" / "DescriptionMap.json"
        with open(desc_json_path, "r", encoding="utf-8") as f:
            self.instance_desc_map = json.load(f)
        # pre-compute instance_name embedding of every node
        self.embeddings, self.node_ids = self._precompute_embeddings()
        # construct the FAISS index (dimension = d)
        self.d = self.embeddings.shape[1]
        self.index = faiss.IndexFlatIP(self.d)              # Inner product (cosine similarity) (normalized vectors)
        faiss.normalize_L2(self.embeddings)
        self.index.add(self.embeddings)

    def _load_nodes(self):
        with open(self.progen_world_path, "r", encoding="utf-8") as f:
            world_data = json.load(f)
        return world_data.get("nodes", [])

    def _precompute_embeddings(self):
        instance_names = [node.get("instance_name", "") for node in self.nodes]
        descriptions = [self.instance_desc_map.get(name, name) for name in instance_names]
        embeddings = self.model.encode(descriptions, convert_to_numpy=True, show_progress_bar=True)
        faiss.normalize_L2(embeddings)
        return embeddings, instance_names

    def retrieve_reference_assets(self, reference_asset_query: str, top_k: int = 50, similarity_threshold: float = 0.5):
        query_embedding = self.model.encode([reference_asset_query], convert_to_numpy=True)
        faiss.normalize_L2(query_embedding)

        D, I = self.index.search(query_embedding, top_k)    # D: similarity score，I: corresponding index
        
        candidate_nodes = []
        for score, idx in zip(D[0], I[0]):
            if score >= similarity_threshold:
                candidate_nodes.append((self.nodes[idx], float(score)))
        if not candidate_nodes:
            print("Cannot find the reference asset")
            return None
        return candidate_nodes
