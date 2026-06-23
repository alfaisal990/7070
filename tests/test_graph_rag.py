import os
import tempfile
import pytest
from ai_project.models.model import PhoenixTransformer, PhoenixModelArgs
from ai_project.tokenizer.tokenizer_trainer import PhoenixTokenizer
from ai_project.memory.vector_db import PhoenixMemoryStore

def test_graph_rag_triples_and_retrieval():
    import torch
    import numpy as np
    import random
    torch.manual_seed(0)
    np.random.seed(0)
    random.seed(0)

    with tempfile.TemporaryDirectory() as tmpdir:
        # Create a dummy tokenizer
        dummy_code = "Alice works at Google. Google is located in Mountain View. Phoenix is a powerful coding system."
        code_file = os.path.join(tmpdir, "code.py")
        with open(code_file, "w", encoding="utf-8") as f:
            f.write(dummy_code)
        tokenizer = PhoenixTokenizer.train([code_file], vocab_size=100, save_dir=tmpdir)

        # Setup model
        args = PhoenixModelArgs(
            vocab_size=100,
            n_layers=1,
            dim=64,
            n_heads=2,
            hidden_dim=128,
            max_seq_len=32
        )
        model = PhoenixTransformer(args)
        
        db_path = os.path.join(tmpdir, "test_kg_db.json")
        store = PhoenixMemoryStore(model, tokenizer, db_path=db_path)
        
        # 1. Test manual relationship insertion
        store.add_kg_relationship("Phoenix", "is a", "powerful coding system")
        assert "phoenix" in store.kg_graph
        assert store.kg_graph["phoenix"] == [["is a", "powerful coding system"]]
        
        # 2. Test extraction from added memories
        # "Subject works at Object" pattern
        store.add_memory("Alice works at Google. Google is located in Mountain View.")
        
        assert "alice" in store.kg_graph
        assert store.kg_graph["alice"] == [["works at", "Google"]]
        
        assert "google" in store.kg_graph
        assert store.kg_graph["google"] == [["is located in", "Mountain View"]]
        
        # 3. Test GraphRAG search
        # Querying for Alice should trigger neighborhood retrieval for Alice and Google
        results = store.search_graph_rag("Who is Alice and where does she work?", top_n=2)
        
        assert len(results) > 0
        top_match_text = results[0]["text"]
        assert "Graph Context:" in top_match_text
        assert "- Alice works at Google" in top_match_text
        assert "- Google is located in Mountain View" in top_match_text
        
        # 4. Test loading from disk loads the relationships
        store_loaded = PhoenixMemoryStore(model, tokenizer, db_path=db_path)
        assert "alice" in store_loaded.kg_graph
        assert store_loaded.kg_graph["alice"] == [["works at", "Google"]]
