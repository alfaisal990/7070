import os
import ast
import random
import hashlib
import glob
from pathlib import Path
import numpy as np

def clean_code(content: str) -> str:
    """
    Normalizes line endings to LF and ensures the Python code is syntactically valid.
    Returns the cleaned code string if valid, otherwise returns None.
    """
    # Normalize line endings
    cleaned = content.replace("\r\n", "\n").replace("\r", "\n")
    
    # Verify syntax
    try:
        ast.parse(cleaned)
        return cleaned
    except SyntaxError:
        return None

def process_and_split_data(src_paths, dest_dir="ai_project/data", train_ratio=0.8, val_ratio=0.1):
    """
    Cleans, deduplicates, and splits source files into train, validation, and test sets.
    """
    raw_dir = Path(dest_dir) / "raw"
    cleaned_dir = Path(dest_dir) / "cleaned"
    
    os.makedirs(raw_dir, exist_ok=True)
    os.makedirs(cleaned_dir, exist_ok=True)
    
    unique_hashes = set()
    cleaned_file_paths = []
    
    for i, path in enumerate(src_paths):
        try:
            with open(path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
            
            cleaned = clean_code(content)
            if cleaned is None:
                continue
                
            # Content-based deduplication
            h = hashlib.sha256(cleaned.encode("utf-8")).hexdigest()
            if h in unique_hashes:
                continue
            unique_hashes.add(h)
            
            # Generate deterministic name to avoid conflict
            save_name = f"code_{i:06d}.py"
            
            raw_path = raw_dir / save_name
            cleaned_path = cleaned_dir / save_name
            
            with open(raw_path, "w", encoding="utf-8") as f:
                f.write(content)
            with open(cleaned_path, "w", encoding="utf-8") as f:
                f.write(cleaned)
                
            cleaned_file_paths.append(str(cleaned_path))
        except Exception as e:
            # Silently skip file read/write issues
            pass
            
    # Split dataset
    random.seed(42)
    random.shuffle(cleaned_file_paths)
    
    total = len(cleaned_file_paths)
    train_end = int(total * train_ratio)
    val_end = train_end + int(total * val_ratio)
    
    train_files = cleaned_file_paths[:train_end]
    val_files = cleaned_file_paths[train_end:val_end]
    test_files = cleaned_file_paths[val_end:]
    
    print(f"Pipeline: Processed {total} unique valid files.")
    print(f"Dataset split -> Train: {len(train_files)}, Val: {len(val_files)}, Test: {len(test_files)}")
    
    return train_files, val_files, test_files

def tokenize_and_save(file_paths, tokenizer, split_name, dest_dir="ai_project/data/tokenized"):
    """
    Tokenizes a list of files using the custom tokenizer and saves the combined
    output as a flat uint16 NumPy array file (.npy).
    """
    os.makedirs(dest_dir, exist_ok=True)
    all_tokens = []
    
    for path in file_paths:
        try:
            with open(path, "r", encoding="utf-8") as f:
                content = f.read()
            
            # Encode and append EOS token
            tokens = tokenizer.encode(content)
            all_tokens.extend(tokens)
            all_tokens.append(tokenizer.eos_id)
        except Exception as e:
            pass
            
    # Save as uint16 numpy binary (supports vocab sizes up to 65,535)
    arr = np.array(all_tokens, dtype=np.uint16)
    out_path = os.path.join(dest_dir, f"{split_name}.npy")
    np.save(out_path, arr)
    print(f"Saved {split_name} tokens to {out_path} (Total tokens: {len(arr)})")
    return out_path
