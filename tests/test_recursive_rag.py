import os
import pytest
import tempfile
from ai_project.tokenizer.tokenizer_trainer import PhoenixTokenizer
from ai_project.models.model import PhoenixTransformer, PhoenixModelArgs
from ai_project.memory.vector_db import PhoenixMemoryStore
from ai_project.memory.rag import PhoenixRAGPipeline

def test_recursive_chunking_logic():
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
        pipeline = PhoenixRAGPipeline(store)

        # Test recursive splitting:
        # text has paragraphs, lines, and words.
        text = "Paragraph 1 line 1.\nParagraph 1 line 2.\n\nParagraph 2 line 1."
        
        # If chunk_size is 40, it should fit "Paragraph 1 line 1.\nParagraph 1 line 2." (length 39)
        # and "Paragraph 2 line 1." (length 19) separately.
        # It should split at "\n\n" first.
        chunks = pipeline.recursive_chunk_text(text, chunk_size=40, chunk_overlap=0)
        assert len(chunks) == 2
        assert chunks[0] == "Paragraph 1 line 1.\nParagraph 1 line 2."
        assert chunks[1] == "Paragraph 2 line 1."

        # If chunk_size is 20, it should split at "\n\n" first, and then the first paragraph (len 39)
        # must be recursively split at "\n" into two chunks of length 19 each.
        chunks = pipeline.recursive_chunk_text(text, chunk_size=20, chunk_overlap=0)
        assert len(chunks) == 3
        assert chunks[0] == "Paragraph 1 line 1."
        assert chunks[1] == "Paragraph 1 line 2."
        assert chunks[2] == "Paragraph 2 line 1."

        # Test empty text and invalid inputs
        assert pipeline.recursive_chunk_text("") == []
        with pytest.raises(ValueError):
            pipeline.recursive_chunk_text("abc", chunk_size=0)
        with pytest.raises(ValueError):
            pipeline.recursive_chunk_text("abc", chunk_size=10, chunk_overlap=10)
