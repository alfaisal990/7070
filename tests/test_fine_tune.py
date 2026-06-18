import os
import json
import pytest
import tempfile
import torch
from ai_project.training.fine_tune import SFTDataset
from ai_project.tokenizer.tokenizer_trainer import PhoenixTokenizer
from ai_project.models.model import PhoenixTransformer, PhoenixModelArgs

def test_sft_dataset_masking_and_padding():
    with tempfile.TemporaryDirectory() as tmpdir:
        # 1. Create a dummy tokenizer
        dummy_code = "x = 1\n"
        code_file = os.path.join(tmpdir, "code.py")
        with open(code_file, "w", encoding="utf-8") as f:
            f.write(dummy_code)
        tokenizer = PhoenixTokenizer.train([code_file], vocab_size=100, save_dir=tmpdir)

        # 2. Create a dummy instruction dataset JSON
        mock_data = [
            {
                "instruction": "Print test",
                "response": "print('test')"
            }
        ]
        json_path = os.path.join(tmpdir, "dataset.json")
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(mock_data, f)

        # 3. Instantiate SFTDataset
        max_seq_len = 128
        dataset = SFTDataset(json_path, tokenizer, max_seq_len)
        
        assert len(dataset) == 1
        x, y = dataset[0]
        
        assert x.shape == (max_seq_len,)
        assert y.shape == (max_seq_len,)
        
        # System & user prompt tokens should be masked (-1 in target y)
        # Assistant response tokens should be positive token IDs
        # Padding tokens should be -1 in target y
        
        # Verify first few elements in target are indeed -1 (masked prompt)
        assert y[0] == -1
        assert y[1] == -1
        
        # Verify there are some positive elements representing response tokens
        response_tokens = y[y > -1]
        assert len(response_tokens) > 0
        
        # Verify that last elements representing pads are masked
        assert y[-1] == -1
