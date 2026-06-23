import os
import pytest
import tempfile
from ai_project.tokenizer.tokenizer_trainer import PhoenixTokenizer
from ai_project.models.model import PhoenixTransformer, PhoenixModelArgs
from ai_project.memory.vector_db import PhoenixMemoryStore

def test_memory_store_retrieval():
    with tempfile.TemporaryDirectory() as tmpdir:
        # 1. Create a dummy tokenizer
        dummy_code = "print('hello')\n"
        code_file = os.path.join(tmpdir, "code.py")
        with open(code_file, "w", encoding="utf-8") as f:
            f.write(dummy_code)
        tokenizer = PhoenixTokenizer.train([code_file], vocab_size=100, save_dir=tmpdir)

        # 2. Setup model
        args = PhoenixModelArgs(
            vocab_size=100,
            n_layers=1,
            dim=32,
            n_heads=2,
            hidden_dim=64,
            max_seq_len=64
        )
        model = PhoenixTransformer(args)
        model.eval()

        # 3. Instantiate memory store
        db_path = os.path.join(tmpdir, "memory.json")
        store = PhoenixMemoryStore(model, tokenizer, db_path=db_path, device="cpu")

        # 4. Add memories
        store.add_memory("Python functions are defined using def keyword.", {"category": "python"})
        store.add_memory("Rust is a systems programming language focused on memory safety.", {"category": "rust"})
        store.add_memory("Binary search has a logarithmic time complexity of O(log n).", {"category": "algorithms"})

        assert len(store.memories) == 3

        # 5. Search memories
        results = store.search_memories("How do I write a function in Python?", top_n=1)
        assert len(results) == 1
        # It should rank the Python-related memory as the top result
        assert "def keyword" in results[0]["text"]
        assert results[0]["metadata"]["category"] == "python"

        # 6. Verify reload from disk
        new_store = PhoenixMemoryStore(model, tokenizer, db_path=db_path, device="cpu")
        assert len(new_store.memories) == 3
        assert new_store.memories[0]["text"] == store.memories[0]["text"]
