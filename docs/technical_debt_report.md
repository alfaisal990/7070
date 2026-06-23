# Phoenix AGI — Technical Debt Report (v7.0.0)

This report reviews the current technical debt, design tradeoffs, and code improvements within the Phoenix AGI codebase.

---

## 1. Tradeoffs & Simplifications

### 1.1 Simulated Quantization vs Hardware Quantization
- **Current implementation**: Weight quantization in `QuantizedLinear` is simulated (i.e. we store weights as uint8 indices, but dequantize them to floats on-the-fly during forward passes).
- **Debt**: Dequantization on-the-fly does not reduce actual GPU memory consumption or execution time during active inference since the forward pass still runs in standard float representations. True INT4/INT8 kernel execution requires hardware-accelerated bindings (e.g. `bitsandbytes` or custom CUDA kernels).
- **Mitigation**: Simulated quantization allows testing model accuracy and precision decay at lower bitwidths without hardware-dependent library locks. Address in the [Platform Improvement Plan](file:///c:/Users/1/Desktop/7070/docs/improvement_plan.md).

### 1.2 Vector Database Scale limit
- **Current implementation**: Cosine similarity is vectorized via PyTorch matrix-vector multiplication (`torch.mv`) over a loaded JSON file cache. Hybrid search overlays a standard sparse BM25 index on top.
- **Debt**: Storing all memories in a flat JSON file loaded into memory works well for thousands of items but will degrade in speed and memory footprint as document databases grow to millions of chunks.
- **Mitigation**: Introduce hierarchical vector indexing (HNSW) or an external sqlite/vector db library once database entries exceed 100,000 records.

### 1.3 Speculative Decoding Draft Model
- **Current implementation**: Speculative decoding is supported using a dynamically initialized base-architecture draft model with `n_layers=1` and small dimensions.
- **Debt**: Generating candidates with a random/untrained draft model will result in low token acceptance rates, meaning inference speedups will only be achieved when using a properly pre-trained draft model.
- **Mitigation**: Support passing an external, pre-trained draft model checkpoint to `generate_speculative`.

---

## 2. Code Quality & Formatting
- **Type Annotations**: Core modules are typed, but some dynamic components (like agent step lists and parsing results) are untyped.
- **Error Propagation**: Standard API routes handle exceptions with a blanket `except Exception as e` raising `HTTPException(status_code=500)`. More granular error handling will prevent information leakage.
