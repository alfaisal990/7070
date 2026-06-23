import os
import json
import argparse
import time
import torch
from torch.amp import GradScaler, autocast
from torch.utils.data import Dataset, DataLoader

from ai_project.models.model import PhoenixTransformer, PhoenixModelArgs
from ai_project.tokenizer.tokenizer_trainer import PhoenixTokenizer

class SFTDataset(Dataset):
    def __init__(self, json_path, tokenizer, max_seq_len):
        self.samples = []
        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            
        for item in data:
            input_ids, targets = self.tokenize_sample(item, tokenizer, max_seq_len)
            self.samples.append((
                torch.tensor(input_ids, dtype=torch.long),
                torch.tensor(targets, dtype=torch.long)
            ))
            
    def tokenize_sample(self, item, tokenizer, max_seq_len):
        system_text = "<|system|>\nYou are a helpful Python coding assistant.\n"
        user_text = f"<|user|>\n{item['instruction']}\n"
        assistant_prefix = "<|assistant|>\n"
        
        # Tokenize segments
        sys_ids = tokenizer.encode(system_text)
        user_ids = tokenizer.encode(user_text)
        prefix_ids = tokenizer.encode(assistant_prefix)
        resp_ids = tokenizer.encode(item['response'])
        eos_ids = [tokenizer.eos_id]
        
        prompt_ids = sys_ids + user_ids + prefix_ids
        response_ids = resp_ids + eos_ids
        
        input_ids = prompt_ids + response_ids
        
        if len(input_ids) > max_seq_len:
            input_ids = input_ids[:max_seq_len]
            prompt_len = min(len(prompt_ids), max_seq_len)
        else:
            prompt_len = len(prompt_ids)
            
        # Target tokens: -1 is ignored in PyTorch CrossEntropyLoss
        targets = [-1] * prompt_len + input_ids[prompt_len:]
        
        # Pad sequence
        padding_len = max_seq_len - len(input_ids)
        if padding_len > 0:
            input_ids = input_ids + [tokenizer.pad_id] * padding_len
            targets = targets + [-1] * padding_len
            
        return input_ids, targets

    def __len__(self):
        return len(self.samples)

    def __getitem__(self, idx):
        return self.samples[idx]

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset_path", type=str, required=True)
    parser.add_argument("--tokenizer_path", type=str, required=True)
    parser.add_argument("--ckpt_path", type=str, required=True)
    parser.add_argument("--out_dir", type=str, default="ai_project/training/sft_checkpoints")
    parser.add_argument("--epochs", type=int, default=3)
    parser.add_argument("--batch_size", type=int, default=4)
    parser.add_argument("--learning_rate", type=float, default=5e-5)
    parser.add_argument("--max_seq_len", type=int, default=1024)
    parser.add_argument("--device", type=str, default="cuda")
    parser.add_argument("--lora_r", type=int, default=0, help="LoRA rank. If > 0, LoRA fine-tuning is enabled.")
    parser.add_argument("--lora_alpha", type=int, default=16, help="LoRA alpha scaling factor.")
    
    args = parser.parse_args()
    device = args.device if torch.cuda.is_available() else "cpu"
    print(f"SFT: Training on device: {device}")
    
    os.makedirs(args.out_dir, exist_ok=True)
    
    # Load custom tokenizer
    tokenizer = PhoenixTokenizer(tokenizer_path=args.tokenizer_path)
    
    # Load dataset
    dataset = SFTDataset(args.dataset_path, tokenizer, args.max_seq_len)
    dataloader = DataLoader(dataset, batch_size=args.batch_size, shuffle=True)
    
    # Load model from checkpoint
    if not os.path.exists(args.ckpt_path):
        print(f"Error: Base checkpoint not found at {args.ckpt_path}")
        return
        
    print(f"SFT: Loading base model checkpoint from {args.ckpt_path}")
    checkpoint = torch.load(args.ckpt_path, map_location=device, weights_only=False)
    
    model_args = checkpoint["model_args"]
    model = PhoenixTransformer(model_args).to(device)
    model.load_state_dict(checkpoint["model_state"])
    
    # Apply LoRA if requested
    if args.lora_r > 0:
        from ai_project.models.model import apply_lora_to_model
        trainable_params = apply_lora_to_model(model, r=args.lora_r, alpha=args.lora_alpha)
        print(f"SFT: Applied LoRA (r={args.lora_r}, alpha={args.lora_alpha}). Trainable parameters: {trainable_params}")
    else:
        print("SFT: Performing full-parameter SFT training.")
        
    optimizer = torch.optim.AdamW([p for p in model.parameters() if p.requires_grad], lr=args.learning_rate, weight_decay=0.01)
    scaler = GradScaler(device=device, enabled=(device == "cuda"))
    
    model.train()
    print("SFT: Starting instruction fine-tuning...")
    
    for epoch in range(args.epochs):
        t0 = time.time()
        epoch_loss = 0.0
        
        for batch_idx, (x, y) in enumerate(dataloader):
            x, y = x.to(device), y.to(device)
            
            optimizer.zero_grad(set_to_none=True)
            with autocast(device_type="cuda" if device == "cuda" else "cpu", enabled=(device == "cuda")):
                # The model computes SFT loss directly when targets are passed
                _, loss = model(x, y)
                
            scaler.scale(loss).backward()
            scaler.unscale_(optimizer)
            torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
            scaler.step(optimizer)
            scaler.update()
            
            epoch_loss += loss.item()
            
        dt = time.time() - t0
        avg_loss = epoch_loss / len(dataloader)
        print(f"Epoch {epoch+1}/{args.epochs} | Avg Loss: {avg_loss:.4f} | Epoch Time: {dt:.1f}s")
        
        # Save SFT checkpoint
        sft_checkpoint = {
            "model_state": model.state_dict(),
            "model_args": model_args,
            "epoch": epoch,
            "args": args,
            "lora_r": getattr(args, "lora_r", 0),
            "lora_alpha": getattr(args, "lora_alpha", 0),
        }
        torch.save(sft_checkpoint, os.path.join(args.out_dir, "sft_latest.pt"))
        print(f"Saved SFT checkpoint for epoch {epoch+1}")
        
    print("SFT: Tuning complete.")

if __name__ == "__main__":
    main()
