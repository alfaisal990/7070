import os
import tempfile
import torch
from ai_project.tokenizer.tokenizer_trainer import PhoenixTokenizer
from ai_project.models.model import PhoenixTransformer, PhoenixModelArgs
from ai_project.inference.engine import PhoenixInferenceEngine

def main():
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
            max_seq_len=32
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
            max_seq_len=32
        )
        draft_model = PhoenixTransformer(draft_args)
        draft_model.eval()
        draft_model.is_trained = True

        prompt = "print("
        wrapped_prompt = f"<|system|>\nYou are a helpful Python coding assistant.\n<|user|>\n{prompt}\n<|assistant|>\n"
        tokens = tokenizer.encode(wrapped_prompt)
        print("WRAPPED TOKENS:", tokens)
        print("WRAPPED tokens_tensor shape:", torch.tensor([tokens]).shape)
        
        # Test base model forward with wrapped tokens
        print("Running base model forward with wrapped tokens...")
        try:
            tokens_tensor = torch.tensor([tokens], dtype=torch.long)
            logits, _ = base_model(tokens_tensor, use_cache=True, start_pos=0)
            print("Base model forward success! logits shape:", logits.shape)
        except Exception as e:
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    main()
