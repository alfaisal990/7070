import torch
import torch.nn as nn
from ai_project.models.model import LoRALinear, merge_lora_weights

# Set seed
torch.manual_seed(42)

# Create a base linear layer
base = nn.Linear(10, 20, bias=True)
lora = LoRALinear(base, r=4, alpha=8)
lora.eval()

# Initialize adapter weights to non-zero values
nn.init.normal_(lora.lora_A, std=0.1)
nn.init.normal_(lora.lora_B, std=0.1)

# Input tensor
x = torch.randn(3, 10)

# Evaluate forward before merging
with torch.no_grad():
    out_lora = lora(x)

# Perform merge
with torch.no_grad():
    delta_w = (lora.lora_B @ lora.lora_A) * lora.scaling
    # Check shape
    print(f"lora_B shape: {lora.lora_B.shape}")
    print(f"lora_A shape: {lora.lora_A.shape}")
    print(f"base weight shape: {base.weight.shape}")
    print(f"delta_w shape: {delta_w.shape}")
    
    # Merged weight
    merged_weight = base.weight + delta_w
    
    # Calculate output using merged weight
    out_merged_manual = torch.nn.functional.linear(x, merged_weight, base.bias)

print(f"Max diff manual vs lora: {torch.max(torch.abs(out_lora - out_merged_manual)).item()}")
