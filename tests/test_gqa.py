import torch
from ai_project.models.model import PhoenixTransformer, PhoenixModelArgs, Attention

def test_gqa_dimensions_and_forward():
    # Setup args with GQA: 8 query heads, 2 key-value heads
    args = PhoenixModelArgs(
        vocab_size=100,
        n_layers=2,
        dim=64,
        n_heads=8,
        n_kv_heads=2,
        hidden_dim=128,
        max_seq_len=32
    )
    model = PhoenixTransformer(args)
    model.eval()

    # Check wk and wv projection dimension
    # head_dim = dim // n_heads = 64 // 8 = 8
    # wk, wv out_features should be n_kv_heads * head_dim = 2 * 8 = 16
    for layer in model.layers:
        attn = layer.attention
        assert attn.n_kv_heads == 2
        assert attn.head_dim == 8
        assert attn.wk.out_features == 16
        assert attn.wv.out_features == 16

    # Forward pass checks
    x = torch.randint(0, 100, (2, 10))
    with torch.no_grad():
        logits, _ = model(x)
    assert logits.shape == (2, 10, 100)

def test_gqa_caching_and_kv_repeats():
    args = PhoenixModelArgs(
        vocab_size=100,
        n_layers=1,
        dim=32,
        n_heads=4,
        n_kv_heads=2,
        hidden_dim=64,
        max_seq_len=32
    )
    model = PhoenixTransformer(args)
    model.eval()

    tokens = torch.randint(0, 100, (1, 5))
    
    # 1. Full forward pass
    with torch.no_grad():
        full_logits, _ = model(tokens)

    # 2. Caching forward pass step-by-step
    with torch.no_grad():
        # Precompute RoPE
        # Prefill first 3 tokens
        prefill_tokens = tokens[:, :3]
        prefill_logits, _ = model(prefill_tokens, use_cache=True, start_pos=0)
        
        # Verify prefill cache shapes
        for layer in model.layers:
            attn = layer.attention
            # cache shape: (batch_size, seq_len, n_kv_heads, head_dim) -> (1, 3, 2, 8)
            assert attn.cache_k is not None
            assert attn.cache_k.shape == (1, 3, 2, 8)
            assert attn.cache_v.shape == (1, 3, 2, 8)

        # Generate next 2 tokens one by one
        for i in range(2):
            pos = 3 + i
            next_token = tokens[:, pos : pos + 1]
            step_logits, _ = model(next_token, use_cache=True, start_pos=pos)
            
            # Verify cache grew correctly
            for layer in model.layers:
                attn = layer.attention
                assert attn.cache_k.shape == (1, pos + 1, 2, 8)

            # Check logits matching
            torch.testing.assert_close(step_logits, full_logits[:, pos : pos + 1], rtol=1e-5, atol=1e-5)
