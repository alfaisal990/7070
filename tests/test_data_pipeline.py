import os
import pytest
import tempfile
import numpy as np
from pathlib import Path
from ai_project.data.data_pipeline import clean_code, process_and_split_data, tokenize_and_save
from ai_project.tokenizer.tokenizer_trainer import PhoenixTokenizer

def test_clean_code():
    # Valid python code
    valid_code = "def add(a, b):\n    return a + b\n"
    assert clean_code(valid_code) == valid_code

    # Invalid python code (syntax error)
    invalid_code = "def add(a, b\n    return a + b"
    assert clean_code(invalid_code) is None

    # CRLF conversion
    crlf_code = "def sub(a, b):\r\n    return a - b\r\n"
    assert clean_code(crlf_code) == "def sub(a, b):\n    return a - b\n"

def test_process_and_split():
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create some source files
        src_dir = Path(tmpdir) / "sources"
        os.makedirs(src_dir)
        
        valid_files = []
        for i in range(10):
            f_path = src_dir / f"test_{i}.py"
            with open(f_path, "w", encoding="utf-8") as f:
                f.write(f"def func_{i}():\n    return {i}\n")
            valid_files.append(str(f_path))
            
        # Add a duplicate file
        dup_path = src_dir / "dup.py"
        with open(dup_path, "w", encoding="utf-8") as f:
            f.write("def func_0():\n    return 0\n")
        valid_files.append(str(dup_path))
        
        # Add an invalid syntax file
        bad_path = src_dir / "bad.py"
        with open(bad_path, "w", encoding="utf-8") as f:
            f.write("def bad_func(:\n    pass")
        valid_files.append(str(bad_path))

        dest_dir = Path(tmpdir) / "output"
        train, val, test = process_and_split_data(
            src_paths=valid_files,
            dest_dir=str(dest_dir),
            train_ratio=0.6,
            val_ratio=0.2
        )
        
        # There should be exactly 10 unique valid files (duplicate and invalid files ignored)
        assert len(train) == 6
        assert len(val) == 2
        assert len(test) == 2

        # Verify raw and cleaned folders are created
        assert os.path.exists(dest_dir / "raw")
        assert os.path.exists(dest_dir / "cleaned")

def test_tokenize_and_save():
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create tokenizer
        dummy_code = "x = 42\n"
        code_file = os.path.join(tmpdir, "code.py")
        with open(code_file, "w", encoding="utf-8") as f:
            f.write(dummy_code)
            
        tokenizer = PhoenixTokenizer.train([code_file], vocab_size=100, save_dir=tmpdir)
        
        # Cleaned files list
        cleaned_files = [code_file]
        
        # Tokenize and save
        tokenized_dir = os.path.join(tmpdir, "tokenized")
        out_path = tokenize_and_save(cleaned_files, tokenizer, "train", dest_dir=tokenized_dir)
        
        # Check output file exists
        assert os.path.exists(out_path)
        
        # Read the file back
        loaded = np.load(out_path)
        assert len(loaded) > 0
        assert loaded[-1] == tokenizer.eos_id
