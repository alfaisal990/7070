import os
import tempfile
import torch
from ai_project.tokenizer.tokenizer_trainer import PhoenixTokenizer
from ai_project.models.model import PhoenixTransformer, PhoenixModelArgs
from ai_project.inference.engine import PhoenixInferenceEngine

def test_speculative_decoding():
    with tempfile.TemporaryDirectory() as tmpdir:
        dummy_code = "print('hello')\n"
        code_file = os.path.join(tmpdir, "code.py")
        with open(code_file, "w", encoding="utf-8") as f:
            f.write(dummy_code)
        tokenizer = PhoenixTokenizer.train([code_file], vocab_size=100, save_dir=tmpdir)

        base_args = PhoenixModelArgs(
            vocab_size=100,
            n_layers=2,
            dim=32,
            n_heads=2,
            hidden_dim=64,
            max_seq_len=256
        )
        base_model = PhoenixTransformer(base_args)
        base_model.eval()
        base_model.is_trained = True

        draft_args = PhoenixModelArgs(
            vocab_size=100,
            n_layers=1,
            dim=32,
            n_heads=2,
            hidden_dim=32,
            max_seq_len=256
        )
        draft_model = PhoenixTransformer(draft_args)
        draft_model.eval()
        draft_model.is_trained = True

        engine = PhoenixInferenceEngine(base_model, tokenizer, device="cpu")
        
        # Test speculative generation
        prompt = "print("
        output = engine.generate_speculative_full(prompt, draft_model=draft_model, max_new_tokens=5, K=2)
        assert isinstance(output, str)
        assert len(output) > 0
