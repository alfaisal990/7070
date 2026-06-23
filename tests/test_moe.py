import torch
import pytest
from ai_project.models.model import PhoenixTransformer, PhoenixModelArgs, apply_lora_to_model, quantize_model_weights, MoEFeedForward

def test_moe_routing_and_forward():
    args = PhoenixModelArgs(
        vocab_size=1000,
        n_layers=2,
        dim=128,
        n_heads=4,
        hidden_dim=256,
        max_seq_len=64,
        num_experts=4,
        moe_top_k=2
    )
    model = PhoenixTransformer(args)
    
    # Assert model has MoEFeedForward layers
    moe_ffn_found = False
    for layer in model.layers:
        if isinstance(layer.feed_forward, MoEFeedForward):
            moe_ffn_found = True
            assert layer.feed_forward.num_experts == 4
            assert layer.feed_forward.moe_top_k == 2
    assert moe_ffn_found, "MoEFeedForward FFN not found in MoE model layers!"

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
    
    # Check that gradient propagates back to gating layers
    loss.backward()
    gate_grad = model.layers[0].feed_forward.gate.weight.grad
    assert gate_grad is not None, "Gradient did not propagate to gating layer"
    assert torch.any(gate_grad != 0), "Gating layer gradient is zero"

def test_moe_lora_application():
    args = PhoenixModelArgs(
        vocab_size=100,
        n_layers=1,
        dim=64,
        n_heads=2,
        hidden_dim=128,
        max_seq_len=32,
        num_experts=3,
        moe_top_k=1
    )
    model = PhoenixTransformer(args)
    trainable_params = apply_lora_to_model(model, r=4, alpha=8)
    
    # Verify that base weights are frozen
    assert not model.layers[0].feed_forward.experts[0].w1.linear.weight.requires_grad
    assert not model.layers[0].feed_forward.experts[0].w3.linear.weight.requires_grad
        
    # Check that adapter parameters are trainable
    lora_a_found = False
    for p_name, p in model.named_parameters():
        if "lora_A" in p_name:
            assert p.requires_grad
            lora_a_found = True
    assert lora_a_found

def test_moe_quantization():
    args = PhoenixModelArgs(
        vocab_size=100,
        n_layers=1,
        dim=64,
        n_heads=2,
        hidden_dim=128,
        max_seq_len=32,
        num_experts=3,
        moe_top_k=1
    )
    model = PhoenixTransformer(args)
    quantized_model = quantize_model_weights(model, bits=8)
    
    # Assert FFN layers inside experts are QuantizedLinear
    from ai_project.models.model import QuantizedLinear
    assert isinstance(quantized_model.layers[0].feed_forward.experts[0].w1, QuantizedLinear)
    assert isinstance(quantized_model.layers[0].feed_forward.gate, QuantizedLinear)
