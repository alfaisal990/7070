import torch
from ai_project.models.model import Attention, PhoenixModelArgs, PhoenixTransformer

def test_sliding_window_attention_mask():
    # Instantiate attention layer with window_size = 2
    # head_dim = 16, n_heads = 2, dim = 32
    att = Attention(dim=32, n_heads=2, window_size=2)
    att.eval()
    
    # Input tensor shape: (batch_size, seqlen, dim) = (1, 4, 32)
    x = torch.randn(1, 4, 32)
    cos = torch.ones(4, 8)
    sin = torch.zeros(4, 8)
    
    # Run forward pass without cache
    out = att(x, cos, sin, use_cache=False, start_pos=0)
    assert out.shape == (1, 4, 32)
    
    # Run with cache
    att.cache_k = None
    att.cache_v = None
    
    # Step 1: prefill step 0 to 2
    # sequence length 3, window_size 2
    out1 = att(x[:, :3, :], cos[:3], sin[:3], use_cache=True, start_pos=0)
    # Cache should be trimmed to the last window_size=2 tokens
    assert att.cache_k.shape[1] == 2
    assert att.cache_v.shape[1] == 2
    
    # Step 2: append 4th token at start_pos = 3
    out2 = att(x[:, 3:, :], cos[3:], sin[3:], use_cache=True, start_pos=3)
    # Cache should remain trimmed to window_size=2 tokens
    assert att.cache_k.shape[1] == 2
    assert att.cache_v.shape[1] == 2

def test_sliding_window_transformer():
    args = PhoenixModelArgs(
        vocab_size=100,
        n_layers=2,
        dim=32,
        n_heads=2,
        hidden_dim=64,
        max_seq_len=32,
        window_size=4
    )
    model = PhoenixTransformer(args)
    model.eval()
    
    tokens = torch.randint(0, 100, (1, 10))
    logits, _ = model(tokens, use_cache=False)
    assert logits.shape == (1, 10, 100)
