import os
import time
import tempfile
from ai_project.tokenizer.tokenizer_trainer import PhoenixTokenizer
from ai_project.models.model import PhoenixTransformer, PhoenixModelArgs
from ai_project.memory.vector_db import PhoenixMemoryStore

def test_memory_lifecycle_tracking_and_consolidation():
    with tempfile.TemporaryDirectory() as tmpdir:
        dummy_code = "print('hello')\n"
        code_file = os.path.join(tmpdir, "code.py")
        with open(code_file, "w", encoding="utf-8") as f:
            f.write(dummy_code)
        tokenizer = PhoenixTokenizer.train([code_file], vocab_size=100, save_dir=tmpdir)

        args = PhoenixModelArgs(
            vocab_size=100,
            n_layers=1,
            dim=16,
            n_heads=1,
            hidden_dim=32,
            max_seq_len=32
        )
        model = PhoenixTransformer(args)
        model.eval()

        store = PhoenixMemoryStore(model, tokenizer, db_path=os.path.join(tmpdir, "db.json"), device="cpu")

        # 1. Test tracking initialization
        store.add_memory("First test memory block.", {"category": "test"})
        assert len(store.memories) == 1
        meta = store.memories[0]["metadata"]
        assert meta["access_count"] == 1
        assert meta["importance"] == 1.0
        assert "last_accessed" in meta

        # 2. Test retrieval updates
        # Searching should retrieve the memory and boost its access_count/importance
        results = store.search_memories("First test memory block", top_n=1)
        assert len(results) == 1
        meta_after = store.memories[0]["metadata"]
        assert meta_after["access_count"] == 2
        assert meta_after["importance"] == 1.1

        # 3. Test Consolidation (Merging similar memories)
        # Add another memory that is highly similar
        store.add_memory("First test memory block duplicated.", {"category": "test"})
        assert len(store.memories) == 2
        
        # Run consolidation (similarity threshold 0.8)
        report = store.consolidate_memories(similarity_threshold=0.8)
        assert report["merged_count"] == 1
        assert len(store.memories) == 1
        
        consolidated = store.memories[0]
        # Text should be combined
        assert "First test memory block." in consolidated["text"]
        assert "First test memory block duplicated." in consolidated["text"]
        # Access count should be summed (2 + 1 = 3)
        assert consolidated["metadata"]["access_count"] == 3

def test_memory_expiration():
    with tempfile.TemporaryDirectory() as tmpdir:
        dummy_code = "print('hello')\n"
        code_file = os.path.join(tmpdir, "code.py")
        with open(code_file, "w", encoding="utf-8") as f:
            f.write(dummy_code)
        tokenizer = PhoenixTokenizer.train([code_file], vocab_size=100, save_dir=tmpdir)

        args = PhoenixModelArgs(
            vocab_size=100,
            n_layers=1,
            dim=16,
            n_heads=1,
            hidden_dim=32,
            max_seq_len=32
        )
        model = PhoenixTransformer(args)
        model.eval()

        store = PhoenixMemoryStore(model, tokenizer, db_path=os.path.join(tmpdir, "db.json"), device="cpu")

        now = time.time()
        
        # Add three memories:
        # Memory 1: Old and low access -> should expire
        store.add_memory("Old inactive memory record.")
        store.memories[0]["metadata"]["last_accessed"] = now - 500
        store.memories[0]["metadata"]["access_count"] = 1
        store.memories[0]["metadata"]["importance"] = 1.0

        # Memory 2: Old but high importance -> should be preserved
        store.add_memory("Old highly important memory record.")
        store.memories[1]["metadata"]["last_accessed"] = now - 500
        store.memories[1]["metadata"]["access_count"] = 1
        store.memories[1]["metadata"]["importance"] = 3.0

        # Memory 3: New memory -> should be preserved
        store.add_memory("Fresh memory record.")
        store.memories[2]["metadata"]["last_accessed"] = now
        store.memories[2]["metadata"]["access_count"] = 1
        store.memories[2]["metadata"]["importance"] = 1.0

        # Run expiration with age threshold = 100 seconds
        report = store.expire_memories(max_age_seconds=100, min_access=2)
        assert report["expired_count"] == 1
        assert len(store.memories) == 2
        
        # Verify which memories remain
        remaining_texts = [m["text"] for m in store.memories]
        assert "Old inactive memory record." not in remaining_texts
        assert "Old highly important memory record." in remaining_texts
        assert "Fresh memory record." in remaining_texts
