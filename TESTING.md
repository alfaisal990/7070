# Testing Guide

Phoenix AI uses `pytest` for backend unit testing. All tests are located inside the `tests/` directory.

## Running Tests

To run the full suite of unit and integration tests:

```powershell
.venv\Scripts\pytest
```

## Test Coverage

The test suite covers:
1. **Tokenizer**: `test_tokenizer.py` verifies training, encoding, decoding, and vocab properties.
2. **Dataset & Pipeline**: `test_data_pipeline.py` verifies AST-cleaning and splitting.
3. **Model architecture**: `test_model.py` checks forward passes, RMSNorm, SwiGLU, and KV cache equivalence.
4. **Training**: `test_train.py` checks cosine decay LR scheduler, data loaders, and gradients.
5. **Instruction Tuning**: `test_fine_tune.py` verifies system prompts and training loops.
6. **Inference**: `test_inference.py` checks generation, sampling, and greedy decode.
7. **Vector DB**: `test_vector_db.py` checks cosine similarity and JSON database storage.
8. **Sandbox**: `test_sandbox.py` checks stdout capture, stderr runtime errors, and execution timeouts.
9. **Agent**: `test_agent.py` verifies execution loops and safe path validation.

All 17 tests must pass successfully to certify a release candidate.
