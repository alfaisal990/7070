import os
import json
import torch
from ai_project.models.model import PhoenixTransformer
from ai_project.tokenizer.tokenizer_trainer import PhoenixTokenizer

class PhoenixMemoryStore:
    """
    Semantic Memory Store for Phoenix AI.
    Utilizes the model's own token embeddings to build vector representations
    and performs cosine-similarity search for retrieval.
    """
    def __init__(self, model: PhoenixTransformer, tokenizer: PhoenixTokenizer, db_path: str = "ai_project/memory/memory_db.json", device: str = "cpu"):
        self.model = model
        self.tokenizer = tokenizer
        self.db_path = db_path
        self.device = device
        self.memories = []
        self.load()

    def get_embedding(self, text: str) -> torch.Tensor:
        """
        Generates a normalized semantic embedding vector using the model's embedding weights.
        """
        tokens = self.tokenizer.encode(text)
        if not tokens:
            return torch.zeros(self.model.args.dim, device=self.device)
            
        tokens_tensor = torch.tensor([tokens], dtype=torch.long, device=self.device)
        
        with torch.no_grad():
            # Extract embeddings and compute mean across sequence length
            embeddings = self.model.tok_embeddings(tokens_tensor)  # (1, seqlen, dim)
            mean_emb = embeddings.mean(dim=1).squeeze(0)  # (dim,)
            
        # L2 Normalize
        norm = mean_emb.norm(p=2)
        if norm > 0:
            mean_emb = mean_emb / norm
            
        return mean_emb

    def add_memory(self, text: str, metadata: dict = None):
        """
        Adds a new memory to the vector database.
        """
        emb = self.get_embedding(text)
        memory_item = {
            "text": text,
            "metadata": metadata or {},
            "embedding": emb.cpu().tolist()
        }
        self.memories.append(memory_item)
        self.save()

    def search_memories(self, query: str, top_n: int = 3) -> list[dict]:
        """
        Searches the memory store using cosine similarity.
        """
        if not self.memories:
            return []
            
        query_emb = self.get_embedding(query).cpu()
        
        results = []
        for item in self.memories:
            item_emb = torch.tensor(item["embedding"])
            # Cosine similarity of normalized vectors is simple dot product
            similarity = torch.dot(query_emb, item_emb).item()
            results.append((similarity, item))
            
        # Sort by similarity descending
        results.sort(key=lambda x: x[0], reverse=True)
        return [{"similarity": sim, "text": item["text"], "metadata": item["metadata"]} for sim, item in results[:top_n]]

    def save(self):
        """Saves memory items to disk."""
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        with open(self.db_path, "w", encoding="utf-8") as f:
            json.dump(self.memories, f, indent=4)

    def load(self):
        """Loads memory items from disk."""
        if os.path.exists(self.db_path):
            try:
                with open(self.db_path, "r", encoding="utf-8") as f:
                    self.memories = json.load(f)
            except Exception:
                self.memories = []
