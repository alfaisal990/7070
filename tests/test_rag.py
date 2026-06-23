import os
import pytest
import tempfile
from pathlib import Path
from ai_project.tokenizer.tokenizer_trainer import PhoenixTokenizer
from ai_project.models.model import PhoenixTransformer, PhoenixModelArgs
from ai_project.memory.vector_db import PhoenixMemoryStore
from ai_project.memory.rag import PhoenixRAGPipeline

def test_rag_chunking():
    # Setup simple memory store with no model needed for basic chunk testing
    # But wait, PhoenixRAGPipeline takes a memory_store in __init__
    # We can pass a Mock or a dummy store. Let's create a minimal store.
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create a dummy tokenizer
        dummy_code = "print('hello')\n"
        code_file = os.path.join(tmpdir, "code.py")
        with open(code_file, "w", encoding="utf-8") as f:
            f.write(dummy_code)
        tokenizer = PhoenixTokenizer.train([code_file], vocab_size=100, save_dir=tmpdir)

        # Setup model
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

        db_path = os.path.join(tmpdir, "memory.json")
        store = PhoenixMemoryStore(model, tokenizer, db_path=db_path, device="cpu")
        pipeline = PhoenixRAGPipeline(store)

        # Test empty text
        assert pipeline.chunk_text("") == []

        # Test basic chunking (chunk_size=10, overlap=2)
        text = "abcdefghijklmnop"  # length 16
        # Expected:
        # chunk 1: 0 to 10 -> "abcdefghij"
        # step size: 10 - 2 = 8
        # chunk 2: start=8, end=16 -> "ijklmnop"
        chunks = pipeline.chunk_text(text, chunk_size=10, chunk_overlap=2)
        assert chunks == ["abcdefghij", "ijklmnop"]

        # Test overlap >= size exception
        with pytest.raises(ValueError, match="chunk_overlap must be strictly less than chunk_size"):
            pipeline.chunk_text(text, chunk_size=10, chunk_overlap=10)

        # Test negative chunk size
        with pytest.raises(ValueError, match="chunk_size must be positive"):
            pipeline.chunk_text(text, chunk_size=0, chunk_overlap=2)

def test_rag_ingest_file():
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

        db_path = os.path.join(tmpdir, "memory.json")
        store = PhoenixMemoryStore(model, tokenizer, db_path=db_path, device="cpu")
        pipeline = PhoenixRAGPipeline(store)

        # Create a document to ingest
        doc_path = os.path.join(tmpdir, "sample.txt")
        doc_content = "This is a document for testing RAG chunking and indexing capabilities."
        with open(doc_path, "w", encoding="utf-8") as f:
            f.write(doc_content)

        # Ingest file
        result = pipeline.ingest_file(doc_path, chunk_size=20, chunk_overlap=5)
        assert result["status"] == "success"
        assert result["file_name"] == "sample.txt"
        assert result["chunks_count"] > 1

        # Check memory store contains the indexed chunks
        assert len(store.memories) == result["chunks_count"]
        for idx, m in enumerate(store.memories):
            assert m["metadata"]["source"] == "sample.txt"
            assert m["metadata"]["chunk_idx"] == idx
            assert m["metadata"]["total_chunks"] == len(store.memories)
            assert m["metadata"]["type"] == "document"
            assert len(m["text"]) <= 20

        # Ingesting missing file should raise FileNotFoundError
        with pytest.raises(FileNotFoundError):
            pipeline.ingest_file(os.path.join(tmpdir, "missing.txt"))
