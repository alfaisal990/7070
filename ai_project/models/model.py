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
    n_kv_heads: int = None  # Grouped-Query Attention head count
    hidden_dim: int = 1376  # Sized for SwiGLU to get ~54M params with weight-tying
    max_seq_len: int = 1024
    window_size: int = None  # Sliding Window Attention window size
    num_experts: int = None
    moe_top_k: int = 2

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


class MoEFeedForward(nn.Module):
    def __init__(self, dim: int, hidden_dim: int, num_experts: int, moe_top_k: int = 2):
        super().__init__()
        self.num_experts = num_experts
        self.moe_top_k = moe_top_k
        self.gate = nn.Linear(dim, num_experts, bias=False)
        self.experts = nn.ModuleList([FeedForward(dim, hidden_dim) for _ in range(num_experts)])

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        orig_shape = x.shape
        x_flat = x.view(-1, orig_shape[-1])
        
        # Compute gating logits (num_tokens, num_experts)
        gate_logits = self.gate(x_flat)
        gate_probs = nn.functional.softmax(gate_logits, dim=-1)
        
        # Select top-k experts
        top_k_probs, top_k_indices = torch.topk(gate_probs, self.moe_top_k, dim=-1)
        
        # Re-normalize the selected top-k weights
        top_k_probs = top_k_probs / (top_k_probs.sum(dim=-1, keepdim=True) + 1e-6)
        
        out = torch.zeros_like(x_flat)
        
        for i, expert in enumerate(self.experts):
            token_indices, k_indices = torch.where(top_k_indices == i)
            if len(token_indices) > 0:
                tokens_in = x_flat[token_indices]
                tokens_out = expert(tokens_in)
                w = top_k_probs[token_indices, k_indices].unsqueeze(-1)
                out.index_add_(0, token_indices, tokens_out * w)
                
        return out.view(orig_shape)

def repeat_kv(x: torch.Tensor, n_rep: int) -> torch.Tensor:
    """Repeats key/value tensors for Grouped-Query Attention."""
    if n_rep == 1:
        return x
    bsz, seqlen, n_kv_heads, head_dim = x.shape
    return (
        x[:, :, :, None, :]
        .expand(bsz, seqlen, n_kv_heads, n_rep, head_dim)
        .reshape(bsz, seqlen, n_kv_heads * n_rep, head_dim)
    )

class Attention(nn.Module):
    def __init__(self, dim: int, n_heads: int, n_kv_heads: int = None, window_size: int = None):
        super().__init__()
        self.n_heads = n_heads
        self.n_kv_heads = n_kv_heads if n_kv_heads is not None else n_heads
        self.head_dim = dim // n_heads
        self.window_size = window_size
        
        self.wq = nn.Linear(dim, dim, bias=False)
        self.wk = nn.Linear(dim, self.n_kv_heads * self.head_dim, bias=False)
        self.wv = nn.Linear(dim, self.n_kv_heads * self.head_dim, bias=False)
        self.wo = nn.Linear(dim, dim, bias=False)
        
        # Key-Value Caching for inference
        self.cache_k = None
        self.cache_v = None

    def forward(self, x: torch.Tensor, cos: torch.Tensor, sin: torch.Tensor, use_cache: bool = False, start_pos: int = 0) -> torch.Tensor:
        bsz, seqlen, _ = x.shape
        
        # Project tokens
        xq = self.wq(x).view(bsz, seqlen, self.n_heads, self.head_dim)
        xk = self.wk(x).view(bsz, seqlen, self.n_kv_heads, self.head_dim)
        xv = self.wv(x).view(bsz, seqlen, self.n_kv_heads, self.head_dim)
        
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
                
            # Trim KV cache if window_size is specified
            if self.window_size is not None:
                self.cache_k = self.cache_k[:, -self.window_size:]
                self.cache_v = self.cache_v[:, -self.window_size:]
                
            keys = self.cache_k
            values = self.cache_v
        else:
            keys = xk
            values = xv
            
        # Repeat key/value heads for GQA
        n_rep = self.n_heads // self.n_kv_heads
        keys = repeat_kv(keys, n_rep)
        values = repeat_kv(values, n_rep)
        
        # Reshape for scaled dot-product attention
        # Shape: (bsz, n_heads, seqlen, head_dim)
        xq = xq.transpose(1, 2)
        keys = keys.transpose(1, 2)
        values = values.transpose(1, 2)
        
        # Matmul query and key
        scores = torch.matmul(xq, keys.transpose(-2, -1)) / math.sqrt(self.head_dim)
        
        # Construct the causal and sliding window mask
        if seqlen > 1 or (use_cache and self.window_size is not None):
            key_len = keys.shape[2]
            mask = torch.zeros((seqlen, key_len), device=x.device)
            
            # Map column index j to overall sequence index
            q_idx = start_pos + torch.arange(seqlen, device=x.device).unsqueeze(1) # (seqlen, 1)
            k_idx = (start_pos + seqlen - key_len) + torch.arange(key_len, device=x.device).unsqueeze(0) # (1, key_len)
            
            # Causal mask: block future tokens
            causal_mask = k_idx > q_idx
            mask = mask.masked_fill(causal_mask, float("-inf"))
            
            # Sliding window mask: block tokens older than window_size
            if self.window_size is not None:
                swa_mask = k_idx < (q_idx - self.window_size)
                mask = mask.masked_fill(swa_mask, float("-inf"))
                
            scores = scores + mask
            
        scores = nn.functional.softmax(scores.float(), dim=-1).type_as(xq)
        output = torch.matmul(scores, values)
        
        # Restore shape and project output
        output = output.transpose(1, 2).contiguous().view(bsz, seqlen, -1)
        return self.wo(output)

class TransformerBlock(nn.Module):
    def __init__(self, dim: int, n_heads: int, n_kv_heads: int, hidden_dim: int, window_size: int = None, num_experts: int = None, moe_top_k: int = 2):
        super().__init__()
        self.attention = Attention(dim, n_heads, n_kv_heads, window_size=window_size)
        if num_experts is not None and num_experts > 0:
            self.feed_forward = MoEFeedForward(dim, hidden_dim, num_experts, moe_top_k)
        else:
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
        
        # Ensure GQA parameters are backwards compatible if loaded from old checkpoints
        n_kv_heads = getattr(args, "n_kv_heads", None)
        window_size = getattr(args, "window_size", None)
        num_experts = getattr(args, "num_experts", None)
        moe_top_k = getattr(args, "moe_top_k", 2)
        
        self.layers = nn.ModuleList([
            TransformerBlock(
                args.dim, 
                args.n_heads, 
                n_kv_heads, 
                args.hidden_dim, 
                window_size=window_size,
                num_experts=num_experts,
                moe_top_k=moe_top_k
            ) 
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


class LoRALinear(nn.Module):
    """
    LoRA (Low-Rank Adaptation) wrapper for standard nn.Linear layers.
    Freezes the base layer and adds trainable low-rank adapters A and B.
    """
    def __init__(self, linear: nn.Linear, r: int = 8, alpha: int = 16, dropout: float = 0.05):
        super().__init__()
        self.linear = linear
        self.r = r
        self.alpha = alpha
        self.scaling = alpha / r
        
        # Define A and B parameters
        self.lora_A = nn.Parameter(torch.zeros(r, linear.in_features))
        self.lora_B = nn.Parameter(torch.zeros(linear.out_features, r))
        self.dropout = nn.Dropout(p=dropout)
        
        # Initialize adapter weights
        nn.init.kaiming_uniform_(self.lora_A, a=math.sqrt(5))
        nn.init.zeros_(self.lora_B)
        
        # Freeze base linear layer
        self.linear.weight.requires_grad = False
        if self.linear.bias is not None:
            self.linear.bias.requires_grad = False
            
    def forward(self, x: torch.Tensor) -> torch.Tensor:
        base_out = self.linear(x)
        lora_out = (self.dropout(x) @ self.lora_A.t()) @ self.lora_B.t()
        return base_out + lora_out * self.scaling


def apply_lora_to_model(model: nn.Module, r: int = 8, alpha: int = 16) -> int:
    """
    Wraps linear layers in Attention and FeedForward blocks with LoRALinear modules.
    Freezes the base weights of the model.
    Returns the number of trainable parameters.
    """
    # Freeze all parameters of the base model
    for p in model.parameters():
        p.requires_grad = False
        
    # Replace layers in attention blocks
    for name, module in model.named_modules():
        if isinstance(module, Attention):
            module.wq = LoRALinear(module.wq, r=r, alpha=alpha)
            module.wk = LoRALinear(module.wk, r=r, alpha=alpha)
            module.wv = LoRALinear(module.wv, r=r, alpha=alpha)
            module.wo = LoRALinear(module.wo, r=r, alpha=alpha)
        elif isinstance(module, FeedForward):
            module.w1 = LoRALinear(module.w1, r=r, alpha=alpha)
            module.w3 = LoRALinear(module.w3, r=r, alpha=alpha)
            
    return sum(p.numel() for p in model.parameters() if p.requires_grad)


def merge_lora_weights(model: nn.Module) -> nn.Module:
    """
    Folds the low-rank adapter weights (B @ A * scaling) back into the base linear layers,
    and replaces all LoRALinear modules with standard nn.Linear layers.
    Returns the un-wrapped model.
    """
    def _merge_recursive(module: nn.Module):
        for name, child in list(module.named_children()):
            if isinstance(child, LoRALinear):
                # Compute merged weight
                with torch.no_grad():
                    delta_w = (child.lora_B @ child.lora_A) * child.scaling
                    child.linear.weight.copy_(child.linear.weight + delta_w)
                
                # Unwrap parameters
                child.linear.weight.requires_grad = True
                if child.linear.bias is not None:
                    child.linear.bias.requires_grad = True
                    
                # Replace LoRALinear with the underlying nn.Linear module
                setattr(module, name, child.linear)
            else:
                _merge_recursive(child)
                
    _merge_recursive(model)
    
    # Reset requires_grad=True across the entire model
    for p in model.parameters():
        p.requires_grad = True
        
    return model


class QuantizedLinear(nn.Module):
    """
    Simulated INT4 or INT8 weight quantization for standard nn.Linear layers.
    Saves memory footprint by storing weights as low-bit scale and zero-point parameters.
    """
    def __init__(self, linear: nn.Linear, bits: int = 4):
        super().__init__()
        self.in_features = linear.in_features
        self.out_features = linear.out_features
        self.bits = bits
        self.qmax = (1 << bits) - 1
        
        # Copy bias if present
        self.bias = nn.Parameter(linear.bias.clone()) if linear.bias is not None else None
        
        # Quantize the weights
        with torch.no_grad():
            w = linear.weight.clone().float()
            # Calculate range and scaling
            w_min = w.min(dim=-1, keepdim=True)[0]
            w_max = w.max(dim=-1, keepdim=True)[0]
            
            # Avoid division by zero
            scale = (w_max - w_min) / float(self.qmax)
            scale = torch.clamp(scale, min=1e-8)
            zero_point = torch.round(-w_min / scale)
            
            # Quantize weight matrix
            w_q = torch.clamp(torch.round(w / scale) + zero_point, 0, self.qmax).to(torch.uint8)
            
        self.register_buffer("w_q", w_q)
        self.register_buffer("scale", scale)
        self.register_buffer("zero_point", zero_point)
        
    def forward(self, x: torch.Tensor) -> torch.Tensor:
        # Dequantize weights on-the-fly during forward pass
        w_dequant = (self.w_q.float() - self.zero_point) * self.scale
        # Cast to match inputs precision
        w_dequant = w_dequant.to(x.dtype)
        return nn.functional.linear(x, w_dequant, self.bias)


def quantize_model_weights(model: nn.Module, bits: int = 4) -> nn.Module:
    """
    Recursively replaces all nn.Linear layers in the model with QuantizedLinear.
    """
    def _quantize_recursive(module: nn.Module):
        for name, child in list(module.named_children()):
            if isinstance(child, nn.Linear):
                # Replace with quantized version
                setattr(module, name, QuantizedLinear(child, bits=bits))
            else:
                _quantize_recursive(child)
                
    _quantize_recursive(model)
    return model


