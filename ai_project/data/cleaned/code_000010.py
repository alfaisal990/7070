import torch
import torch.nn as nn
import math
from dataclasses import dataclass

@dataclass
class PhoenixModelArgs:
    vocab_size: int = 32000
    n_layers: int = 12
    dim: int = 512
    n_heads: int = 8
    hidden_dim: int = 1376  # Sized for SwiGLU to get ~54M params with weight-tying
    max_seq_len: int = 1024

class RMSNorm(nn.Module):
    def __init__(self, dim: int, eps: float = 1e-6):
        super().__init__()
        self.eps = eps
        self.weight = nn.Parameter(torch.ones(dim))

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        variance = x.pow(2).mean(-1, keepdim=True)
        return x * torch.rsqrt(variance + self.eps) * self.weight

def precompute_theta_pos_frequencies(head_dim: int, seq_len: int, theta: float = 10000.0) -> tuple[torch.Tensor, torch.Tensor]:
    assert head_dim % 2 == 0
    powers = torch.arange(0, head_dim, 2, dtype=torch.float32) / head_dim
    theta_vals = 1.0 / (theta ** powers)  # Shape: (head_dim / 2,)
    m = torch.arange(seq_len, dtype=torch.float32)  # Shape: (seq_len,)
    freqs = torch.outer(m, theta_vals)  # Shape: (seq_len, head_dim / 2)
    return torch.cos(freqs), torch.sin(freqs)

def reshape_for_broadcast(freqs: torch.Tensor, x: torch.Tensor) -> torch.Tensor:
    ndim = x.ndim
    assert ndim >= 2
    assert freqs.shape == (x.shape[1], x.shape[-1])
    shape = [1 if i != 1 and i != ndim - 1 else x.shape[i] for i in range(ndim)]
    return freqs.view(*shape)

def apply_rotary_emb(x: torch.Tensor, cos: torch.Tensor, sin: torch.Tensor) -> torch.Tensor:
    # x shape: (batch_size, seq_len, num_heads, head_dim)
    # Split the last dimension (head_dim) into pairs
    x_real = x[..., 0::2]
    x_imag = x[..., 1::2]
    
    # Reshape cos and sin to broadcast over batch and heads
    cos = reshape_for_broadcast(cos, x_real)
    sin = reshape_for_broadcast(sin, x_real)
    
    # Complex rotation: (r_out + i_out * j) = (r + i * j) * (cos + sin * j)
    out_real = x_real * cos - x_imag * sin
    out_imag = x_real * sin + x_imag * cos
    
    # Recombine and flatten the pairs
    out = torch.stack([out_real, out_imag], dim=-1)
    return out.flatten(-2)

class FeedForward(nn.Module):
    def __init__(self, dim: int, hidden_dim: int):
        super().__init__()
        # SwiGLU requires 3 linear matrices (gate, up, down)
        self.w1 = nn.Linear(dim, hidden_dim, bias=False)  # Gate projection
        self.w2 = nn.Linear(hidden_dim, dim, bias=False)  # Down projection
        self.w3 = nn.Linear(dim, hidden_dim, bias=False)  # Up projection

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        # SwiGLU: w2( SiLU(w1(x)) * w3(x) )
        return self.w2(nn.functional.silu(self.w1(x)) * self.w3(x))

class Attention(nn.Module):
    def __init__(self, dim: int, n_heads: int):
        super().__init__()
        self.n_heads = n_heads
        self.head_dim = dim // n_heads
        
        self.wq = nn.Linear(dim, dim, bias=False)
        self.wk = nn.Linear(dim, dim, bias=False)
        self.wv = nn.Linear(dim, dim, bias=False)
        self.wo = nn.Linear(dim, dim, bias=False)
        
        # Key-Value Caching for inference
        self.cache_k = None
        self.cache_v = None

    def forward(self, x: torch.Tensor, cos: torch.Tensor, sin: torch.Tensor, use_cache: bool = False, start_pos: int = 0) -> torch.Tensor:
        bsz, seqlen, _ = x.shape
        
        # Project tokens
        xq = self.wq(x).view(bsz, seqlen, self.n_heads, self.head_dim)
        xk = self.wk(x).view(bsz, seqlen, self.n_heads, self.head_dim)
        xv = self.wv(x).view(bsz, seqlen, self.n_heads, self.head_dim)
        
        # Apply Rotary Positional Embeddings
        xq = apply_rotary_emb(xq, cos, sin)
        xk = apply_rotary_emb(xk, cos, sin)
        
        # Caching logic
        if use_cache:
            if start_pos == 0 or self.cache_k is None:
                self.cache_k = xk
                self.cache_v = xv
            else:
                self.cache_k = torch.cat([self.cache_k, xk], dim=1)
                self.cache_v = torch.cat([self.cache_v, xv], dim=1)
            keys = self.cache_k
            values = self.cache_v
        else:
            keys = xk
            values = xv
            
        # Reshape for scaled dot-product attention
        # Shape: (bsz, n_heads, seqlen, head_dim)
        xq = xq.transpose(1, 2)
        keys = keys.transpose(1, 2)
        values = values.transpose(1, 2)
        
        # Matmul query and key
        scores = torch.matmul(xq, keys.transpose(-2, -1)) / math.sqrt(self.head_dim)
        
        # Causal mask application
        if seqlen > 1:
            mask = torch.full((seqlen, seqlen), float("-inf"), device=x.device)
            mask = torch.triu(mask, diagonal=1)
            key_len = keys.shape[2]
            if key_len > seqlen:
                padding = torch.zeros(seqlen, key_len - seqlen, device=x.device)
                mask = torch.cat([padding, mask], dim=-1)
            scores = scores + mask
            
        scores = nn.functional.softmax(scores.float(), dim=-1).type_as(xq)
        output = torch.matmul(scores, values)
        
        # Restore shape and project output
        output = output.transpose(1, 2).contiguous().view(bsz, seqlen, -1)
        return self.wo(output)

class TransformerBlock(nn.Module):
    def __init__(self, dim: int, n_heads: int, hidden_dim: int):
        super().__init__()
        self.attention = Attention(dim, n_heads)
        self.feed_forward = FeedForward(dim, hidden_dim)
        self.attention_norm = RMSNorm(dim)
        self.ffn_norm = RMSNorm(dim)

    def forward(self, x: torch.Tensor, cos: torch.Tensor, sin: torch.Tensor, use_cache: bool = False, start_pos: int = 0) -> torch.Tensor:
        # Pre-normalization with residual connections
        h = x + self.attention(self.attention_norm(x), cos, sin, use_cache, start_pos)
        out = h + self.feed_forward(self.ffn_norm(h))
        return out

class PhoenixTransformer(nn.Module):
    def __init__(self, args: PhoenixModelArgs):
        super().__init__()
        self.args = args
        self.tok_embeddings = nn.Embedding(args.vocab_size, args.dim)
        
        self.layers = nn.ModuleList([
            TransformerBlock(args.dim, args.n_heads, args.hidden_dim) 
            for _ in range(args.n_layers)
        ])
        
        self.norm = RMSNorm(args.dim)
        self.output = nn.Linear(args.dim, args.vocab_size, bias=False)
        
        # Weight-tying to reduce footprint and improve learning stability
        self.output.weight = self.tok_embeddings.weight
        
        # Precompute RoPE frequencies
        cos, sin = precompute_theta_pos_frequencies(args.dim // args.n_heads, args.max_seq_len)
        self.register_buffer("cos_freqs", cos, persistent=False)
        self.register_buffer("sin_freqs", sin, persistent=False)
        
    def forward(self, tokens: torch.Tensor, targets: torch.Tensor = None, use_cache: bool = False, start_pos: int = 0) -> tuple[torch.Tensor, torch.Tensor | None]:
        _, seqlen = tokens.shape
        h = self.tok_embeddings(tokens)
        
        # Extract appropriate segment of RoPE frequencies
        if use_cache:
            cos = self.cos_freqs[start_pos : start_pos + seqlen].to(h.device)
            sin = self.sin_freqs[start_pos : start_pos + seqlen].to(h.device)
        else:
            cos = self.cos_freqs[:seqlen].to(h.device)
            sin = self.sin_freqs[:seqlen].to(h.device)
            
        for layer in self.layers:
            h = layer(h, cos, sin, use_cache, start_pos)
            
        h = self.norm(h)
        logits = self.output(h)
        
        loss = None
        if targets is not None:
            # Shift tokens for next-token prediction
            loss = nn.functional.cross_entropy(
                logits.view(-1, logits.size(-1)),
                targets.view(-1),
                ignore_index=-1
            )
            
        return logits, loss
