import os
import argparse
import time
import math
import numpy as np
import torch
from torch.amp import GradScaler, autocast

from ai_project.models.model import PhoenixTransformer, PhoenixModelArgs
from ai_project.tokenizer.tokenizer_trainer import PhoenixTokenizer

class CausalDataLoader:
    def __init__(self, npy_path, seq_len, batch_size):
        self.data = np.load(npy_path, mmap_mode="r")
        self.seq_len = seq_len
        self.batch_size = batch_size
        self.length = len(self.data)
        
    def close(self):
        if hasattr(self.data, "_mmap") and self.data._mmap is not None:
            self.data._mmap.close()

    def get_batch(self, device):
        # Sample random offsets in the corpus
        max_idx = self.length - self.seq_len - 1
        if max_idx <= 0:
            raise ValueError(f"Corpus size ({self.length}) is too small for context length {self.seq_len}.")
            
        ix = torch.randint(0, max_idx, (self.batch_size,))
        x_list = []
        y_list = []
        
        for i in ix:
            x_seq = torch.from_numpy((self.data[i : i + self.seq_len]).astype(np.int64))
            y_seq = torch.from_numpy((self.data[i + 1 : i + self.seq_len + 1]).astype(np.int64))
            x_list.append(x_seq)
            y_list.append(y_seq)
            
        x = torch.stack(x_list).to(device)
        y = torch.stack(y_list).to(device)
        return x, y

def get_lr(it, lr, warmup_iters, lr_decay_iters, min_lr):
    # Linear warmup
    if it < warmup_iters:
        return lr * it / warmup_iters
    # Constant after decay iters
    if it > lr_decay_iters:
        return min_lr
    # Cosine decay
    decay_ratio = (it - warmup_iters) / (lr_decay_iters - warmup_iters)
    assert 0 <= decay_ratio <= 1
    coeff = 0.5 * (1.0 + math.cos(math.pi * decay_ratio))
    return min_lr + coeff * (lr - min_lr)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--data_dir", type=str, default="ai_project/data/tokenized")
    parser.add_argument("--out_dir", type=str, default="ai_project/training/checkpoints")
    parser.add_argument("--eval_interval", type=int, default=100)
    parser.add_argument("--log_interval", type=int, default=10)
    parser.add_argument("--eval_iters", type=int, default=20)
    
    # Model parameters
    parser.add_argument("--n_layers", type=int, default=12)
    parser.add_argument("--n_heads", type=int, default=8)
    parser.add_argument("--dim", type=int, default=512)
    parser.add_argument("--hidden_dim", type=int, default=1376)
    parser.add_argument("--max_seq_len", type=int, default=1024)
    
    # Training parameters
    parser.add_argument("--batch_size", type=int, default=4)  # Small batch to prevent OOM
    parser.add_argument("--gradient_accumulation_steps", type=int, default=8)  # Simulated batch size = 32
    parser.add_argument("--max_iters", type=int, default=1000)
    parser.add_argument("--learning_rate", type=float, default=3e-4)
    parser.add_argument("--weight_decay", type=float, default=0.1)
    parser.add_argument("--warmup_iters", type=int, default=100)
    parser.add_argument("--lr_decay_iters", type=int, default=1000)
    parser.add_argument("--min_lr", type=float, default=3e-5)
    parser.add_argument("--device", type=str, default="cuda")
    
    args = parser.parse_args()
    
    device = args.device if torch.cuda.is_available() else "cpu"
    print(f"Training on device: {device}")
    
    # Setup paths
    os.makedirs(args.out_dir, exist_ok=True)
    train_npy = os.path.join(args.data_dir, "train.npy")
    val_npy = os.path.join(args.data_dir, "val.npy")
    
    if not os.path.exists(train_npy):
        print(f"Error: Tokenized training dataset not found at {train_npy}. Please run data pipeline first.")
        return
        
    train_loader = CausalDataLoader(train_npy, args.max_seq_len, args.batch_size)
    val_loader = CausalDataLoader(val_npy, args.max_seq_len, args.batch_size) if os.path.exists(val_npy) else None
    
    # Load model
    model_args = PhoenixModelArgs(
        vocab_size=32000,
        n_layers=args.n_layers,
        dim=args.dim,
        n_heads=args.n_heads,
        hidden_dim=args.hidden_dim,
        max_seq_len=args.max_seq_len
    )
    
    model = PhoenixTransformer(model_args).to(device)
    total_params = sum(p.numel() for p in model.parameters() if p.requires_grad)
    print(f"Initialized Phoenix Transformer with {total_params / 1e6:.2f}M parameters.")
    
    # Setup optimizer and AMP scaler
    optimizer = torch.optim.AdamW(model.parameters(), lr=args.learning_rate, weight_decay=args.weight_decay)
    scaler = GradScaler(device=device, enabled=(device == "cuda"))
    
    # Eval loop function
    @torch.no_grad()
    def estimate_loss():
        out = {}
        model.eval()
        for split, loader in [("train", train_loader), ("val", val_loader)]:
            if loader is None:
                continue
            losses = torch.zeros(args.eval_iters)
            for k in range(args.eval_iters):
                x, y = loader.get_batch(device)
                with autocast(device_type="cuda" if device == "cuda" else "cpu", enabled=(device == "cuda")):
                    _, loss = model(x, y)
                losses[k] = loss.item()
            out[split] = losses.mean().item()
        model.train()
        return out
        
    # Start training loop
    iter_num = 0
    t0 = time.time()
    
    model.train()
    
    while iter_num < args.max_iters:
        # Cosine LR decay
        lr = get_lr(iter_num, args.learning_rate, args.warmup_iters, args.lr_decay_iters, args.min_lr)
        for param_group in optimizer.param_groups:
            param_group["lr"] = lr
            
        # Eval
        if iter_num % args.eval_interval == 0 and iter_num > 0:
            losses = estimate_loss()
            val_loss_str = f", Val Loss: {losses['val']:.4f}" if "val" in losses else ""
            print(f"Iter {iter_num}: Train Loss: {losses['train']:.4f}{val_loss_str}")
            
            # Save checkpoint
            checkpoint = {
                "model_state": model.state_dict(),
                "optimizer_state": optimizer.state_dict(),
                "model_args": model_args,
                "iter_num": iter_num,
                "args": args
            }
            ckpt_path = os.path.join(args.out_dir, f"ckpt_iter_{iter_num}.pt")
            torch.save(checkpoint, ckpt_path)
            # Link latest checkpoint
            torch.save(checkpoint, os.path.join(args.out_dir, "ckpt_latest.pt"))
            print(f"Saved checkpoint to {ckpt_path}")
            
        # Forward/Backward
        optimizer.zero_grad(set_to_none=True)
        loss_accum = 0.0
        
        for micro_step in range(args.gradient_accumulation_steps):
            x, y = train_loader.get_batch(device)
            with autocast(device_type="cuda" if device == "cuda" else "cpu", enabled=(device == "cuda")):
                _, loss = model(x, y)
                # Scale loss to account for gradient accumulation
                loss = loss / args.gradient_accumulation_steps
                loss_accum += loss.item()
            scaler.scale(loss).backward()
            
        # Clip grads and step
        scaler.unscale_(optimizer)
        torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
        scaler.step(optimizer)
        scaler.update()
        
        t1 = time.time()
        dt = t1 - t0
        t0 = t1
        
        if iter_num % args.log_interval == 0:
            print(f"Iter {iter_num:4d} | Loss: {loss_accum * args.gradient_accumulation_steps:.4f} | LR: {lr:.2e} | Step Time: {dt*1000:.1f}ms")
            
        iter_num += 1

if __name__ == "__main__":
    main()
