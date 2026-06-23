import os
import pytest
import tempfile
import numpy as np
import torch
from ai_project.training.train import CausalDataLoader, get_lr
from ai_project.models.model import PhoenixTransformer, PhoenixModelArgs

def test_dataloader():
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create a dummy tokenized corpus (.npy)
        tokens = np.arange(100, dtype=np.uint16)
        npy_path = os.path.join(tmpdir, "train.npy")
        np.save(npy_path, tokens)
        
        # Instantiate Loader
        seq_len = 10
        batch_size = 2
        loader = CausalDataLoader(npy_path, seq_len=seq_len, batch_size=batch_size)
        
        x, y = loader.get_batch("cpu")
        assert x.shape == (batch_size, seq_len)
        assert y.shape == (batch_size, seq_len)
        
        # Verify next-token shifting
        for b in range(batch_size):
            torch.testing.assert_close(x[b, 1:], y[b, :-1])
            
        loader.close()

def test_lr_scheduler():
    lr = 3e-4
    warmup = 10
    decay = 100
    min_lr = 3e-5
    
    # During warmup
    assert get_lr(0, lr, warmup, decay, min_lr) == 0.0
    assert get_lr(5, lr, warmup, decay, min_lr) == lr * 0.5
    assert get_lr(10, lr, warmup, decay, min_lr) == lr
    
    # After decay
    assert get_lr(150, lr, warmup, decay, min_lr) == min_lr

def test_mini_training_loop():
    with tempfile.TemporaryDirectory() as tmpdir:
        # 1. Create a tiny dummy corpus
        tokens = np.random.randint(0, 100, size=200, dtype=np.uint16)
        train_npy = os.path.join(tmpdir, "train.npy")
        np.save(train_npy, tokens)
        
        # 2. Setup args
        args = PhoenixModelArgs(
            vocab_size=100,
            n_layers=1,
            dim=16,
            n_heads=2,
            hidden_dim=32,
            max_seq_len=10
        )
        
        # Initialize model & loader
        model = PhoenixTransformer(args).to("cpu")
        loader = CausalDataLoader(train_npy, seq_len=args.max_seq_len, batch_size=2)
        optimizer = torch.optim.AdamW(model.parameters(), lr=1e-3)
        
        # 3. Perform 3 steps of training
        initial_loss = None
        final_loss = None
        
        for step in range(3):
            x, y = loader.get_batch("cpu")
            logits, loss = model(x, y)
            
            if step == 0:
                initial_loss = loss.item()
                
            optimizer.zero_grad()
            loss.backward()
            optimizer.step()
            
            if step == 2:
                final_loss = loss.item()
                
        # Gradient updates should happen, loss value should be computed successfully
        assert initial_loss is not None
        assert final_loss is not None

        # 4. Check checkpoint save/load equivalence
        checkpoint = {
            "model_state": model.state_dict(),
            "model_args": args
        }
        ckpt_path = os.path.join(tmpdir, "ckpt.pt")
        torch.save(checkpoint, ckpt_path)
        
        loaded = torch.load(ckpt_path, map_location="cpu", weights_only=False)
        loaded_model = PhoenixTransformer(loaded["model_args"]).to("cpu")
        loaded_model.load_state_dict(loaded["model_state"])
        
        # Output should match
        x, _ = loader.get_batch("cpu")
        with torch.no_grad():
            logits_orig, _ = model(x)
            logits_load, _ = loaded_model(x)
            
        torch.testing.assert_close(logits_orig, logits_load)
        
        loader.close()
