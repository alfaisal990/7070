import os
import torch
from ai_project.models.model import PhoenixTransformer, PhoenixModelArgs
from ai_project.tokenizer.tokenizer_trainer import PhoenixTokenizer
from ai_project.inference.engine import PhoenixInferenceEngine

def main():
    tokenizer_path = "ai_project/tokenizer/tokenizer.json"
    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"Using device: {device}")
    
    tokenizer = PhoenixTokenizer(tokenizer_path=tokenizer_path)
    args = PhoenixModelArgs()
    # Initialize a blank model (same as API does when no checkpoint)
    model = PhoenixTransformer(args).to(device)
    model.eval()
    
    engine = PhoenixInferenceEngine(model, tokenizer, device=device)
    
    try:
        print("Testing generate_stream('Hello')...")
        for chunk in engine.generate_stream("Hello", temperature=0.7):
            print(chunk, end="", flush=True)
        print("\nStream completed successfully.")
    except Exception as e:
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
