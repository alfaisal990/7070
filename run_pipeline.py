import os
import glob
from pathlib import Path

from ai_project.data.data_pipeline import process_and_split_data, tokenize_and_save
from ai_project.tokenizer.tokenizer_trainer import PhoenixTokenizer

def main():
    print("=== Phoenix AI: Starting Data & Tokenizer Pipeline ===")
    
    # 1. Gather all python source files from the project
    workspace_dir = Path("c:/Users/1/Desktop/7070").resolve()
    py_files = []
    
    # Search in ai_project and tests
    for root, dirs, files in os.walk(workspace_dir / "ai_project"):
        # Skip cache directories
        if "__pycache__" in root or "dashboard" in root or "data" in root:
            continue
        for file in files:
            if file.endswith(".py"):
                py_files.append(os.path.join(root, file))
                
    for root, dirs, files in os.walk(workspace_dir / "tests"):
        if "__pycache__" in root:
            continue
        for file in files:
            if file.endswith(".py"):
                py_files.append(os.path.join(root, file))
                
    print(f"Found {len(py_files)} Python source files in project to use as dataset.")
    
    if not py_files:
        print("Error: No source files found to train on.")
        return

    # 2. Run Data split and cleaning (Stage 1 & 2)
    train_files, val_files, test_files = process_and_split_data(
        src_paths=py_files,
        dest_dir="ai_project/data",
        train_ratio=0.8,
        val_ratio=0.1
    )
    
    # 3. Train the Tokenizer on the cleaned files (Stage 3)
    # Get all cleaned files for training
    cleaned_dir = Path("ai_project/data/cleaned")
    cleaned_files = [str(p) for p in cleaned_dir.glob("*.py")]
    
    print(f"Training tokenizer on {len(cleaned_files)} cleaned python files...")
    tokenizer = PhoenixTokenizer.train(
        files=cleaned_files,
        vocab_size=32000,
        min_frequency=1,  # Set frequency to 1 to allow small corpus training
        save_dir="ai_project/tokenizer"
    )
    
    # 4. Tokenize and save datasets to NumPy flat binary (Stage 4)
    print("Tokenizing train split...")
    tokenize_and_save(train_files, tokenizer, "train", dest_dir="ai_project/data/tokenized")
    
    print("Tokenizing validation split...")
    tokenize_and_save(val_files, tokenizer, "val", dest_dir="ai_project/data/tokenized")
    
    print("Tokenizing test split...")
    tokenize_and_save(test_files, tokenizer, "test", dest_dir="ai_project/data/tokenized")
    
    print("=== Pipeline Complete: Tokenizer trained and datasets prepared ===")

if __name__ == "__main__":
    main()
