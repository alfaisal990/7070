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
        self.device = device
        self.memories = []
        self.kg_graph = {}
        self._embeddings_cache = None
        
        # Resolve database path relative to workspace root if not absolute
        if not os.path.isabs(db_path):
            workspace_root = os.environ.get("PHOENIX_WORKSPACE", "c:/Users/1/Desktop/7070")
            db_path = os.path.join(workspace_root, db_path)
        self.db_path = os.path.abspath(db_path)
        
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

    def _update_tensor_cache(self):
        """Updates the cached PyTorch tensor of all embeddings for fast vectorized search."""
        if not self.memories:
            self._embeddings_cache = None
            return
            
        embeddings_list = [item["embedding"] for item in self.memories]
        self._embeddings_cache = torch.tensor(embeddings_list, dtype=torch.float32, device=self.device)

    def add_memory(self, text: str, metadata: dict = None):
        """
        Adds a new memory to the vector database.
        """
        import time
        emb = self.get_embedding(text)
        meta = metadata or {}
        
        # Initialize tracking metrics in metadata
        if "access_count" not in meta:
            meta["access_count"] = 1
        if "last_accessed" not in meta:
            meta["last_accessed"] = time.time()
        if "importance" not in meta:
            meta["importance"] = 1.0
            
        memory_item = {
            "text": text,
            "metadata": meta,
            "embedding": emb.cpu().tolist()
        }
        self.memories.append(memory_item)
        self._update_tensor_cache()
        
        # Extract and add KG relations
        triples = self.extract_kg_triples(text)
        for src, rel, tgt in triples:
            src_key = src.strip().lower()
            if src_key not in self.kg_graph:
                self.kg_graph[src_key] = []
            rel_tuple = [rel.strip(), tgt.strip()]
            if rel_tuple not in self.kg_graph[src_key]:
                self.kg_graph[src_key].append(rel_tuple)
                
        self.save()

    def search_memories(self, query: str, top_n: int = 3) -> list[dict]:
        """
        Searches the memory store using cosine similarity.
        """
        if not self.memories:
            return []
            
        query_emb = self.get_embedding(query)
        
        # Build or synchronize tensor cache
        if (self._embeddings_cache is None or 
            self._embeddings_cache.shape[0] != len(self.memories) or 
            self._embeddings_cache.shape[1] != self.model.args.dim):
            self._update_tensor_cache()
            
        if self._embeddings_cache is None:
            return []
            
        with torch.no_grad():
            # Cosine similarity for normalized vectors is a single matrix-vector multiplication
            similarities = torch.mv(self._embeddings_cache, query_emb)
            similarities_list = similarities.cpu().tolist()
            
        results = []
        for sim, item in zip(similarities_list, self.memories):
            results.append((sim, item))
            
        # Sort by similarity descending
        results.sort(key=lambda x: x[0], reverse=True)
        
        # Update metrics for top retrieved items
        import time
        for sim, item in results[:top_n]:
            meta = item.setdefault("metadata", {})
            meta["access_count"] = meta.get("access_count", 0) + 1
            meta["last_accessed"] = time.time()
            # Dynamic importance boost based on access frequency
            meta["importance"] = min(5.0, meta.get("importance", 1.0) + 0.1)
            
        self.save()
            
        return [{"similarity": sim, "text": item["text"], "metadata": item["metadata"]} for sim, item in results[:top_n]]

    def consolidate_memories(self, similarity_threshold: float = 0.85) -> dict:
        """
        Consolidates memories by merging duplicate or highly similar memories.
        """
        if len(self.memories) < 2:
            return {"merged_count": 0, "remaining_count": len(self.memories)}
            
        if (self._embeddings_cache is None or 
            self._embeddings_cache.shape[0] != len(self.memories) or 
            self._embeddings_cache.shape[1] != self.model.args.dim):
            self._update_tensor_cache()
            
        merged_indices = set()
        new_memories = []
        
        for i in range(len(self.memories)):
            if i in merged_indices:
                continue
                
            item_i = self.memories[i]
            emb_i = torch.tensor(item_i["embedding"], dtype=torch.float32, device=self.device)
            
            similar_indices = []
            for j in range(i + 1, len(self.memories)):
                if j in merged_indices:
                    continue
                item_j = self.memories[j]
                emb_j = torch.tensor(item_j["embedding"], dtype=torch.float32, device=self.device)
                
                with torch.no_grad():
                    sim = torch.dot(emb_i, emb_j).item()
                    
                if sim >= similarity_threshold:
                    similar_indices.append(j)
                    
            if similar_indices:
                merged_text = item_i["text"]
                meta_i = item_i.get("metadata", {})
                
                total_access = meta_i.get("access_count", 1)
                max_importance = meta_i.get("importance", 1.0)
                
                for idx in similar_indices:
                    item_idx = self.memories[idx]
                    meta_idx = item_idx.get("metadata", {})
                    
                    if item_idx["text"] not in merged_text:
                        merged_text += " | " + item_idx["text"]
                        
                    total_access += meta_idx.get("access_count", 1)
                    max_importance = max(max_importance, meta_idx.get("importance", 1.0))
                    merged_indices.add(idx)
                    
                meta_i["access_count"] = total_access
                meta_i["importance"] = max_importance
                
                # Apply Semantic Compression if combined text length exceeds 300 characters
                if len(merged_text) > 300:
                    compressed = self._compress_text(merged_text)
                    meta_i["compressed"] = True
                    meta_i["original_length"] = len(merged_text)
                    merged_text = compressed
                    
                item_i["text"] = merged_text
                item_i["embedding"] = self.get_embedding(merged_text).cpu().tolist()
                
            new_memories.append(item_i)
            
        merged_count = len(self.memories) - len(new_memories)
        self.memories = new_memories
        self._update_tensor_cache()
        self.save()
        
        return {
            "merged_count": merged_count,
            "remaining_count": len(self.memories)
        }

    def _compress_text(self, text: str) -> str:
        """
        Compresses text by summarization using the LLM.
        Falls back to rule-based extractive compression if model is untrained / mock mode.
        """
        if not getattr(self.model, "is_trained", False):
            # Fallback compression: Extractive sentence-based summarization
            parts = [p.strip() for p in text.split("|") if p.strip()]
            if len(parts) > 1:
                p1 = parts[0]
                p2 = parts[-1]
                if len(p1) > 120:
                    p1 = p1[:117] + "..."
                if len(p2) > 120:
                    p2 = p2[:117] + "..."
                return f"Consolidated Memory: {p1} ... {p2}"
            sentences = [s.strip() for s in text.replace("\n", " ").split(".") if s.strip()]
            if len(sentences) > 2:
                s1 = sentences[0]
                s2 = sentences[-1]
                if len(s1) > 120:
                    s1 = s1[:117] + "..."
                if len(s2) > 120:
                    s2 = s2[:117] + "..."
                return f"{s1}. {s2}."
            return text[:297] + "..." if len(text) > 300 else text
            
        # If trained, run a lightweight summarization prompt
        prompt = (
            f"<|system|>\nYou are a concise summarizer. Summarize key facts from the text in one short sentence.\n"
            f"<|user|>\nText to summarize:\n{text}\n"
            f"<|assistant|>\nSummary:"
        )
        
        tokens = self.tokenizer.encode(prompt)
        tokens_tensor = torch.tensor([tokens], dtype=torch.long, device=self.device)
        seqlen = tokens_tensor.shape[1]
        
        if seqlen >= self.model.args.max_seq_len:
            return text  # Safe fallback
            
        for layer in self.model.layers:
            layer.attention.cache_k = None
            layer.attention.cache_v = None
            
        with torch.no_grad():
            logits, _ = self.model(tokens_tensor, use_cache=True, start_pos=0)
            next_token = torch.argmax(logits[:, -1, :], dim=-1, keepdim=True)
            
            summary_ids = []
            curr_pos = seqlen
            
            for _ in range(50):
                token_id = next_token.item()
                if token_id == self.tokenizer.eos_id:
                    break
                summary_ids.append(token_id)
                
                next_token_logits, _ = self.model(next_token, use_cache=True, start_pos=curr_pos)
                next_token = torch.argmax(next_token_logits[:, -1, :], dim=-1, keepdim=True)
                curr_pos += 1
                
        decoded = self.tokenizer.decode(summary_ids).strip()
        return decoded if decoded else text

    def expire_memories(self, max_age_seconds: float = 86400, min_access: int = 2) -> dict:
        """
        Prunes memories that are older than max_age_seconds AND have access count < min_access.
        High importance memories (>= 2.5) are preserved and never expire.
        """
        import time
        now = time.time()
        expired_count = 0
        preserved_memories = []
        
        for item in self.memories:
            meta = item.setdefault("metadata", {})
            last_accessed = meta.get("last_accessed", now)
            access_count = meta.get("access_count", 1)
            importance = meta.get("importance", 1.0)
            
            age = now - last_accessed
            
            if age > max_age_seconds and access_count < min_access and importance < 2.5:
                expired_count += 1
            else:
                preserved_memories.append(item)
                
        self.memories = preserved_memories
        self._update_tensor_cache()
        self.save()
        
        return {
            "expired_count": expired_count,
            "remaining_count": len(self.memories)
        }

    def _compute_bm25_scores(self, query: str) -> list[float]:
        import math
        import re
        query_words = re.findall(r"\w+", query.lower())
        if not query_words or not self.memories:
            return [0.0] * len(self.memories)
            
        N = len(self.memories)
        doc_tokens = []
        for m in self.memories:
            doc_tokens.append(re.findall(r"\w+", m["text"].lower()))
            
        doc_lengths = [len(tokens) for tokens in doc_tokens]
        avg_doc_len = sum(doc_lengths) / N if N > 0 else 1.0
        if avg_doc_len == 0:
            avg_doc_len = 1.0
            
        df = {}
        for word in set(query_words):
            df[word] = sum(1 for tokens in doc_tokens if word in tokens)
            
        idf = {}
        for word in query_words:
            n_w = df.get(word, 0)
            idf_val = math.log((N - n_w + 0.5) / (n_w + 0.5) + 1.0)
            idf[word] = max(0.0, idf_val)
            
        k1 = 1.5
        b = 0.75
        
        scores = []
        for i, tokens in enumerate(doc_tokens):
            doc_len = doc_lengths[i]
            tf = {}
            for token in tokens:
                tf[token] = tf.get(token, 0) + 1
                
            score = 0.0
            for word in query_words:
                tf_val = tf.get(word, 0)
                if tf_val > 0:
                    numerator = tf_val * (k1 + 1)
                    denominator = tf_val + k1 * (1.0 - b + b * (doc_len / avg_doc_len))
                    score += idf[word] * (numerator / denominator)
            scores.append(score)
            
        return scores

    def search_memories_hybrid(self, query: str, top_n: int = 3) -> list[dict]:
        if not self.memories:
            return []
            
        # 1. Compute Dense scores
        query_emb = self.get_embedding(query)
        if (self._embeddings_cache is None or 
            self._embeddings_cache.shape[0] != len(self.memories) or 
            self._embeddings_cache.shape[1] != self.model.args.dim):
            self._update_tensor_cache()
            
        dense_sims = []
        if self._embeddings_cache is not None:
            with torch.no_grad():
                similarities = torch.mv(self._embeddings_cache, query_emb)
                dense_sims = similarities.cpu().tolist()
        else:
            dense_sims = [0.0] * len(self.memories)
            
        dense_ranked = sorted(enumerate(dense_sims), key=lambda x: x[1], reverse=True)
        dense_ranks = {idx: rank for rank, (idx, _) in enumerate(dense_ranked)}
        
        # 2. Compute BM25 scores
        bm25_scores = self._compute_bm25_scores(query)
        bm25_ranked = sorted(enumerate(bm25_scores), key=lambda x: x[1], reverse=True)
        bm25_ranks = {idx: rank for rank, (idx, _) in enumerate(bm25_ranked)}
        
        # 3. Reciprocal Rank Fusion (RRF)
        rrf_scores = []
        for idx in range(len(self.memories)):
            dense_rank = dense_ranks[idx]
            bm25_rank = bm25_ranks[idx]
            rrf_score = 1.0 / (60.0 + dense_rank) + 1.0 / (60.0 + bm25_rank)
            rrf_scores.append((rrf_score, idx))
            
        rrf_scores.sort(key=lambda x: x[0], reverse=True)
        
        results = []
        import time
        for score, idx in rrf_scores[:top_n]:
            item = self.memories[idx]
            meta = item.setdefault("metadata", {})
            meta["access_count"] = meta.get("access_count", 0) + 1
            meta["last_accessed"] = time.time()
            meta["importance"] = min(5.0, meta.get("importance", 1.0) + 0.1)
            
            results.append({
                "similarity": score,
                "text": item["text"],
                "metadata": item["metadata"]
            })
            
        self.save()
        return results

    def add_kg_relationship(self, source: str, relation: str, target: str):
        src_key = source.strip().lower()
        if src_key not in self.kg_graph:
            self.kg_graph[src_key] = []
        rel_tuple = [relation.strip(), target.strip()]
        if rel_tuple not in self.kg_graph[src_key]:
            self.kg_graph[src_key].append(rel_tuple)
        self.save()

    def extract_kg_triples(self, text: str) -> list[tuple[str, str, str]]:
        import re
        triples = []
        # Split into sentences or lines
        sentences = re.split(r'[.!?\n]', text)
        
        # Patterns: (source, relation, target)
        patterns = [
            (r'\b(.+?)\b\s+is\s+a(?:n)?\s+\b(.+)\b', 'is a'),
            (r'\b(.+?)\b\s+works\s+at\s+\b(.+)\b', 'works at'),
            (r'\b(.+?)\b\s+developed\s+\b(.+)\b', 'developed'),
            (r'\b(.+?)\b\s+created\s+\b(.+)\b', 'created'),
            (r'\b(.+?)\b\s+is\s+located\s+in\s+\b(.+)\b', 'is located in'),
            (r'\b(.+?)\b\s+is\s+\b(.+)\b', 'is'),
        ]
        
        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue
            for pattern, relation in patterns:
                match = re.search(pattern, sentence, re.IGNORECASE)
                if match:
                    source = match.group(1).strip()
                    target = match.group(2).strip()
                    if 1 < len(source) < 50 and 1 < len(target) < 50:
                        triples.append((source, relation, target))
                        break
        return triples

    def search_graph_rag(self, query: str, top_n: int = 3) -> list[dict]:
        if not self.memories and not self.kg_graph:
            return []
            
        # Get base dense similarities first
        results = self.search_memories(query, top_n=top_n)
        
        # Scan query and results to identify active entities
        active_entities = []
        query_lower = query.lower()
        for entity_key in self.kg_graph.keys():
            if entity_key in query_lower:
                active_entities.append(entity_key)
                continue
            for item in results:
                if entity_key in item["text"].lower():
                    active_entities.append(entity_key)
                    break
                    
        # Gather relations for active entities
        graph_relations = []
        for entity_key in active_entities:
            relations = self.kg_graph.get(entity_key, [])
            for rel, target in relations:
                graph_relations.append(f"{entity_key.title()} {rel} {target}")
                
        # Deduplicate
        seen = set()
        unique_relations = []
        for r_str in graph_relations:
            if r_str not in seen:
                seen.add(r_str)
                unique_relations.append(r_str)
                
        if unique_relations:
            context_block = "Graph Context:\n" + "\n".join(f"- {r}" for r in unique_relations)
            if results:
                results[0]["text"] = f"{results[0]['text']}\n\n{context_block}"
            else:
                results.append({
                    "similarity": 1.0,
                    "text": context_block,
                    "metadata": {"graph_only": True}
                })
                
        return results

    def save(self):
        """Saves memory items and knowledge graph to disk atomically to prevent corruption."""
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        data = {
            "memories": self.memories,
            "kg_graph": self.kg_graph
        }
        temp_path = self.db_path + ".tmp"
        try:
            with open(temp_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=4)
            os.replace(temp_path, self.db_path)
        except Exception as e:
            if os.path.exists(temp_path):
                try:
                    os.remove(temp_path)
                except OSError:
                    pass
            raise e

    def load(self):
        """Loads memory items and knowledge graph from disk."""
        if os.path.exists(self.db_path):
            try:
                with open(self.db_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                if isinstance(data, dict) and "memories" in data:
                    self.memories = data["memories"]
                    self.kg_graph = data.get("kg_graph", {})
                else:
                    self.memories = data if isinstance(data, list) else []
                    self.kg_graph = {}
                self._update_tensor_cache()
            except Exception:
                self.memories = []
                self.kg_graph = {}
                self._embeddings_cache = None
        else:
            self.kg_graph = {}
