import torch
import torch.nn as nn
from ai_project.models.model import PhoenixTransformer, PhoenixModelArgs, apply_lora_to_model, merge_lora_weights, LoRALinear

def test_lora_merge_unwrapping():
    # 1. Setup model with small dimensions for testing
    args = PhoenixModelArgs(
        vocab_size=100,
        n_layers=2,
        dim=64,
        n_heads=4,
        hidden_dim=128,
        max_seq_len=32
    )
    model = PhoenixTransformer(args)
    model.eval()

    # Create random input tokens
    x = torch.randint(0, 100, (2, 10))

    # Get output of base model before any LoRA
    with torch.no_grad():
        logits_base, _ = model(x)

    # 2. Apply LoRA structure
    apply_lora_to_model(model, r=4, alpha=8)
    
    # Verify Attention / FFN projections are now wrapped in LoRALinear
    for name, module in model.named_modules():
        if name.endswith(".wq") or name.endswith(".wo") or name.endswith(".w1"):
            assert isinstance(module, LoRALinear)

    # Simulate fine-tuning by writing non-zero values to some LoRA parameters
    # Let's set lora_B to random weights (since it defaults to zero, which means initially no change)
    for name, module in model.named_modules():
        if isinstance(module, LoRALinear):
            nn.init.normal_(module.lora_A, mean=0.0, std=0.1)
            nn.init.normal_(module.lora_B, mean=0.0, std=0.1)

    # Put model back in eval mode since apply_lora_to_model instantiates new modules in training mode
    model.eval()

    # Output with active LoRA adapters
    with torch.no_grad():
        logits_lora, _ = model(x)

    # 3. Merge weights and unwrap
    merge_lora_weights(model)

    # Output of merged model
    with torch.no_grad():
        logits_merged, _ = model(x)

    # 4. Verify module types are unwrapped back to standard nn.Linear
    for name, module in model.named_modules():
        # wq, wk, wv, wo, w1, w2, w3 should all be plain nn.Linear now
        if name.endswith(".wq") or name.endswith(".wo") or name.endswith(".w1"):
            assert isinstance(module, nn.Linear)
            assert not isinstance(module, LoRALinear)

    # All parameters should have requires_grad=True
    for p in model.parameters():
        assert p.requires_grad

    # The output of the merged model MUST match the output of the model with the LoRA adapters active,
    # because merging mathematically folds the adapters directly into the base weights.
    torch.testing.assert_close(logits_merged, logits_lora, rtol=1e-4, atol=1e-4)

    # The output should NOT be identical to the original base model before LoRA SFT simulation
    # (unless the random SFT weights happen to be exactly zero, which is statistically impossible here)
    assert not torch.allclose(logits_merged, logits_base)
