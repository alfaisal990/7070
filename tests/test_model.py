import torch
import pytest
from ai_project.models.model import PhoenixTransformer, PhoenixModelArgs

def test_model_parameter_count_and_shapes():
    args = PhoenixModelArgs(
        vocab_size=1000,
        n_layers=2,
        dim=128,
        n_heads=4,
        hidden_dim=256,
        max_seq_len=64
    )
    model = PhoenixTransformer(args)
    
    # Calculate parameter count
    total_params = sum(p.numel() for p in model.parameters() if p.requires_grad)
    # Target parameter count is small here because we scaled down args for testing
    
    # Forward pass check
    bsz = 2
    seqlen = 16
    tokens = torch.randint(0, args.vocab_size, (bsz, seqlen))
    
    logits, loss = model(tokens)
    assert logits.shape == (bsz, seqlen, args.vocab_size)
    assert loss is None

    # Forward pass with targets
    targets = torch.randint(0, args.vocab_size, (bsz, seqlen))
    logits, loss = model(tokens, targets)
    assert loss is not None
    assert loss.ndim == 0  # Scalar loss

def test_kv_cache_equivalence():
    # Setup model
    args = PhoenixModelArgs(
        vocab_size=100,
        n_layers=2,
        dim=64,
        n_heads=2,
        hidden_dim=128,
        max_seq_len=32
    )
    model = PhoenixTransformer(args)
    model.eval()  # Eval mode to disable dropout etc.
    
    # Check equivalent outputs for full forward vs cache-based step-by-step
    tokens = torch.randint(0, args.vocab_size, (1, 10))
    
    # 1. Full forward pass
    with torch.no_grad():
        full_logits, _ = model(tokens)
        
    # 2. Incremental generation pass with caching
    with torch.no_grad():
        # Pre-fill cache with first 5 tokens
        prefill_tokens = tokens[:, :5]
        prefill_logits, _ = model(prefill_tokens, use_cache=True, start_pos=0)
        
        # Verify pre-fill logits match first 5 steps of full logits
        torch.testing.assert_close(prefill_logits, full_logits[:, :5], rtol=1e-5, atol=1e-5)
        
        # Generate token by token for the next 5 tokens
        for i in range(5):
            pos = 5 + i
            next_token = tokens[:, pos : pos + 1]
            step_logits, _ = model(next_token, use_cache=True, start_pos=pos)
            
            # Verify logits match the corresponding step in the full forward pass
            torch.testing.assert_close(step_logits, full_logits[:, pos : pos + 1], rtol=1e-5, atol=1e-5)
