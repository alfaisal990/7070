import os
from ai_project.tokenizer.tokenizer_trainer import PhoenixTokenizer

def main():
    tokenizer_path = "ai_project/tokenizer/tokenizer.json"
    print(f"Checking if tokenizer path exists: {os.path.exists(tokenizer_path)}")
    
    try:
        t = PhoenixTokenizer(tokenizer_path=tokenizer_path)
        print("Tokenizer loaded successfully.")
        print(f"Vocab size: {t.get_vocab_size()}")
        print(f"pad_id: {t.pad_id}")
        print(f"eos_id: {t.eos_id}")
        print(f"bos_id: {t.bos_id}")
        
        # Test encoding
        text = "Hello world"
        print(f"Encoding text '{text}': {t.encode(text)}")
        
        # Test encoding with special tokens
        text_with_special = "<|system|>\nYou are helpful.\n<|user|>\nHello\n<|assistant|>\n"
        print(f"Encoding with special tokens: {t.encode(text_with_special)}")
        
    except Exception as e:
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
