import os
import tempfile
from ai_project.tokenizer.tokenizer_trainer import PhoenixTokenizer
from ai_project.models.model import PhoenixTransformer, PhoenixModelArgs
from ai_project.memory.vector_db import PhoenixMemoryStore

def test_hybrid_search_rrf():
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

        # Add memories with specific keyword distributions
        store.add_memory("The system deployment occurred on Friday.")
        store.add_memory("Model weights are quantized using INT4 simulated scaling.")
        store.add_memory("FastAPI endpoint routes API requests safely.")

        # Test BM25 score counts directly
        bm25_scores = store._compute_bm25_scores("deployment")
        assert len(bm25_scores) == 3
        # First document should have higher score for keyword "deployment"
        assert bm25_scores[0] > bm25_scores[1]
        assert bm25_scores[0] > bm25_scores[2]

        # Test Hybrid Search (RRF)
        results = store.search_memories_hybrid("deployment", top_n=2)
        assert len(results) == 2
        # First document should be the top result
        assert "deployment" in results[0]["text"]
