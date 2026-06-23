import os
import json
import numpy as np

class VectorDBMigrationManager:
    """
    Migration manager for Phoenix AI Vector Database.
    Evaluates and formats data for migration from memory_db.json to:
    1. FAISS (Facebook AI Similarity Search)
    2. HNSW (Hierarchical Navigable Small World)
    3. Qdrant (Production Cloud Vector DB)
    """
    def __init__(self, db_path: str = "ai_project/memory/memory_db.json"):
        self.db_path = db_path
        self.memories = []
        self.kg_graph = {}
        self.load()

    def load(self):
        if os.path.exists(self.db_path):
            with open(self.db_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            self.memories = data.get("memories", [])
            self.kg_graph = data.get("kg_graph", {})

    def export_to_faiss(self) -> dict:
        """
        Converts vector embeddings into NumPy float32 format required for FAISS indexing.
        """
        if not self.memories:
            return {"status": "empty", "vectors": None, "payloads": []}
        
        vectors = []
        payloads = []
        for i, m in enumerate(self.memories):
            vectors.append(m["embedding"])
            payloads.append({
                "id": i,
                "text": m["text"],
                "metadata": m["metadata"]
            })
        
        # Convert to float32 NumPy array
        np_vectors = np.array(vectors, dtype=np.float32)
        return {
            "status": "success",
            "vectors_shape": np_vectors.shape,
            "np_vectors": np_vectors,
            "payloads": payloads
        }

    def export_to_hnsw(self) -> dict:
        """
        Prepares embeddings and identifiers for HNSWLib indexing structures.
        """
        export_data = self.export_to_faiss()
        if export_data["status"] == "empty":
            return {"status": "empty", "labels": [], "vectors": None}
            
        labels = np.array([p["id"] for p in export_data["payloads"]], dtype=np.int64)
        return {
            "status": "success",
            "labels": labels,
            "vectors": export_data["np_vectors"],
            "payloads": export_data["payloads"]
        }

    def export_to_qdrant(self) -> list[dict]:
        """
        Formats data into Qdrant PointStruct schema for API bulk upload.
        """
        points = []
        for i, m in enumerate(self.memories):
            points.append({
                "id": i,
                "vector": m["embedding"],
                "payload": {
                    "text": m["text"],
                    "metadata": m["metadata"]
                }
            })
        return points

    def generate_migration_report(self) -> dict:
        """
        Generates database size metrics and migration viability score.
        """
        num_records = len(self.memories)
        if num_records == 0:
            return {"status": "no_data", "records": 0}
            
        dim = len(self.memories[0]["embedding"])
        size_bytes = os.path.getsize(self.db_path) if os.path.exists(self.db_path) else 0
        
        # Determine recommendation based on size
        if num_records < 1000:
            recommendation = "JSON Memory Store (Brute Force Cosine via PyTorch)"
            rationale = "Zero-dependency deployment, local-first execution. Dataset is too small to benefit from index overhead."
        elif 1000 <= num_records < 50000:
            recommendation = "Local HNSW (hnswlib) / FAISS Index"
            rationale = "Local file-based fast approximate search with logarithmic time complexity. No external service required."
        else:
            recommendation = "Qdrant Docker Service / Cloud"
            rationale = "Scale-out capability, horizontal partitioning, payload filtering support, and robust memory management."

        return {
            "num_records": num_records,
            "vector_dimension": dim,
            "db_file_size_kb": round(size_bytes / 1024, 2),
            "recommended_target": recommendation,
            "recommendation_rationale": rationale
        }
