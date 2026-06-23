import os
import tempfile
import time
from ai_project.tokenizer.tokenizer_trainer import PhoenixTokenizer
from ai_project.models.model import PhoenixTransformer, PhoenixModelArgs
from ai_project.memory.vector_db import PhoenixMemoryStore

def test_fallback_memory_compression():
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
        model.is_trained = False

        store = PhoenixMemoryStore(model, tokenizer, db_path=os.path.join(tmpdir, "db.json"), device="cpu")
        
        # Test case 1: Multiple parts split by '|'
        long_text_pipe = "First sentence of information. | Second sentence of information. | Third sentence of information. | " + "A" * 200 + " | Final sentence of information."
        compressed_pipe = store._compress_text(long_text_pipe)
        assert compressed_pipe.startswith("Consolidated Memory: First sentence of information.")
        assert compressed_pipe.endswith("Final sentence of information.")
        
        # Test case 2: Single block of text with sentences, no '|'
        long_text_dot = "First sentence here. Second sentence is located here. Third sentence is over here. " + "B" * 200 + ". Last sentence is here."
        compressed_dot = store._compress_text(long_text_dot)
        assert compressed_dot.startswith("First sentence here.")
        assert compressed_dot.endswith("Last sentence is here.")

def test_consolidation_triggers_compression():
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
        model.is_trained = False

        store = PhoenixMemoryStore(model, tokenizer, db_path=os.path.join(tmpdir, "db.json"), device="cpu")
        
        # Add two highly similar memories whose combined text length > 300 characters
        text1 = "This is a very long memory statement about system architecture and requirements that we need to consolidate. " + "C" * 200
        text2 = "This is a very long memory statement about system architecture and requirements that we need to consolidate. " + "D" * 200
        
        store.add_memory(text1)
        store.add_memory(text2)
        
        # Run consolidation
        report = store.consolidate_memories(similarity_threshold=0.8)
        assert report["merged_count"] == 1
        assert len(store.memories) == 1
        
        consolidated = store.memories[0]
        assert consolidated["metadata"].get("compressed") is True
        assert consolidated["metadata"].get("original_length") > 300
        assert len(consolidated["text"]) < consolidated["metadata"]["original_length"]
