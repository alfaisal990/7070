import torch
import torch.nn as nn
from ai_project.models.model import PhoenixTransformer, PhoenixModelArgs, QuantizedLinear, quantize_model_weights

def test_quantized_linear_layer():
    # 1. Base linear layer
    torch.manual_seed(42)
    base = nn.Linear(32, 64, bias=True)
    
    # 2. Wrap in 4-bit QuantizedLinear
    qlinear = QuantizedLinear(base, bits=4)
    assert qlinear.bits == 4
    assert qlinear.qmax == 15
    assert qlinear.w_q.shape == base.weight.shape
    assert qlinear.w_q.dtype == torch.uint8
    assert qlinear.scale.shape == (64, 1)
    assert qlinear.zero_point.shape == (64, 1)
    
    # Check forward pass
    x = torch.randn(4, 32)
    with torch.no_grad():
        out_base = base(x)
        out_quant = qlinear(x)
        
    assert out_quant.shape == (4, 64)
    # The outputs should be reasonably close (quantization noise is small but present)
    # Check that mean absolute difference is within bounds (e.g. < 0.15)
    mae = torch.mean(torch.abs(out_base - out_quant)).item()
    assert mae < 0.15

def test_model_quantization_wrapper():
    # Setup model
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
    
    x = torch.randint(0, 100, (2, 10))
    with torch.no_grad():
        orig_logits, _ = model(x)
        
    # Apply model-wide quantization
    quantize_model_weights(model, bits=4)
    
    # Verify module replacement
    for name, module in model.named_modules():
        # Check that output and attn projections are now QuantizedLinear
        if name.endswith(".wq") or name.endswith(".wo") or name.endswith(".w1"):
            assert isinstance(module, QuantizedLinear)
            
    # Forward pass on quantized model
    with torch.no_grad():
        quant_logits, _ = model(x)
        
    assert quant_logits.shape == (2, 10, 100)
    # Check that the logits are close enough (mean absolute difference < 1.0)
    mae = torch.mean(torch.abs(orig_logits - quant_logits)).item()
    assert mae < 1.0
