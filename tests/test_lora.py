import torch
import torch.nn as nn
from ai_project.models.model import PhoenixTransformer, PhoenixModelArgs, LoRALinear, apply_lora_to_model

def test_lora_linear_forward():
    # Base linear layer
    base_linear = nn.Linear(32, 64)
    # Wrap in LoRA
    lora_module = LoRALinear(base_linear, r=8, alpha=16)
    
    # Check dimensions
    assert lora_module.lora_A.shape == (8, 32)
    assert lora_module.lora_B.shape == (64, 8)
    
    # Check requires_grad is frozen on base but active on LoRA adapters
    assert not base_linear.weight.requires_grad
    assert lora_module.lora_A.requires_grad
    assert lora_module.lora_B.requires_grad
    
    # Forward pass
    x = torch.randn(4, 32)
    out = lora_module(x)
    assert out.shape == (4, 64)

def test_apply_lora_to_model():
    args = PhoenixModelArgs(vocab_size=100, n_layers=2, dim=64, n_heads=4, hidden_dim=128)
    model = PhoenixTransformer(args)
    
    # Before LoRA: all parameters requires_grad
    total_params = sum(p.numel() for p in model.parameters())
    assert all(p.requires_grad for p in model.parameters())
    
    # Apply LoRA
    trainable_params = apply_lora_to_model(model, r=4, alpha=8)
    
    # Verify parameter freezing
    assert trainable_params < total_params
    assert trainable_params > 0
    
    # Check that attention projection layers are wrapped in LoRALinear
    for name, module in model.named_modules():
        if name.endswith(".wq") or name.endswith(".wo"):
            assert isinstance(module, LoRALinear)
            
    # Forward pass after LoRA
    x = torch.randint(0, 100, (2, 16))
    logits, _ = model(x)
    assert logits.shape == (2, 16, 100)
