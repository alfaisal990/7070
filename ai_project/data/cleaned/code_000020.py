import os
import pytest
import tempfile
import torch
from ai_project.tokenizer.tokenizer_trainer import PhoenixTokenizer
from ai_project.models.model import PhoenixTransformer, PhoenixModelArgs
from ai_project.inference.engine import PhoenixInferenceEngine

def test_inference_engine_generation():
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
            n_layers=2,
            dim=64,
            n_heads=2,
            hidden_dim=128,
            max_seq_len=256
        )
        model = PhoenixTransformer(args)
        model.eval()

        # 3. Instantiate inference engine
        engine = PhoenixInferenceEngine(model, tokenizer, device="cpu")

        # Test full generation
        prompt = "def hello():"
        output_text = engine.generate(prompt, max_new_tokens=10, temperature=0.7)
        assert isinstance(output_text, str)

        # Test streaming generation
        stream = engine.generate_stream(prompt, max_new_tokens=5, temperature=0.0) # Greedy
        chunks = list(stream)
        assert len(chunks) <= 5
        assert all(isinstance(c, str) for c in chunks)
