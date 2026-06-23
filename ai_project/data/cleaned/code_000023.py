import os
import pytest
import tempfile
from ai_project.tokenizer.tokenizer_trainer import PhoenixTokenizer

def test_tokenizer_train_and_roundtrip():
    # 1. Create a dummy Python file to train on
    dummy_code = """
def hello_world():
    print("Hello, world!")
    for i in range(10):
        print(f"Index: {i}")
"""
    with tempfile.TemporaryDirectory() as tmpdir:
        train_file_path = os.path.join(tmpdir, "train_code.py")
        with open(train_file_path, "w", encoding="utf-8") as f:
            f.write(dummy_code)

        # 2. Train the tokenizer
        vocab_size = 100  # Small vocab size for testing
        tokenizer = PhoenixTokenizer.train(
            files=[train_file_path],
            vocab_size=vocab_size,
            min_frequency=1,
            save_dir=tmpdir
        )

        # 3. Assert properties
        assert tokenizer.get_vocab_size() >= len(PhoenixTokenizer.SPECIAL_TOKENS)
        
        # Check special tokens
        for token in PhoenixTokenizer.SPECIAL_TOKENS:
            assert tokenizer.token_to_id(token) is not None

        # 4. Test round-trip encode/decode
        test_text = "def hello_world():\n    print(\"Hello, world!\")"
        encoded = tokenizer.encode(test_text)
        decoded = tokenizer.decode(encoded)
        
        # Since it is byte-level BPE, it should reconstruct exactly
        assert decoded == test_text

        # 5. Check loading from file
        save_path = os.path.join(tmpdir, "tokenizer.json")
        loaded_tokenizer = PhoenixTokenizer(tokenizer_path=save_path)
        assert loaded_tokenizer.get_vocab_size() == tokenizer.get_vocab_size()
        assert loaded_tokenizer.encode(test_text) == encoded
