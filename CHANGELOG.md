# Changelog

All notable changes to Phoenix AI will be documented in this file.

## [7.0.0] - 2026-06-22
### Added
- **Sliding Window Attention (SWA)**: Integrated localized context windows ($W$) in the `Attention` class to minimize KV-cache memory limits during long context generation.
- **Speculative Decoding**: Added `generate_speculative` step validation in the `PhoenixInferenceEngine` to support draft token generation and parallel base validation.
- **Hybrid Dense-Sparse RAG Search**: Added sparse BM25 tf-idf scoring and reciprocal rank fusion (RRF) combining dense similarity rankings inside `vector_db.py`. Supported in search requests.
- **Observability Tracing**: Added correlation tracing IDs (`X-Request-ID`) via FastAPI middleware, logging request identifiers across JSON logs.
- **Expanded Test Coverage**: Added `test_sliding_window_attention.py`, `test_speculative_decoding.py`, and `test_hybrid_search.py` (total now 64 tests passing).

## [6.0.0] - 2026-06-22
### Added
- **Phase 1 Repository Intelligence Reports**: Generated comprehensive architecture, technical debt, security, performance, and missing features reports in the `docs/` directory.
- **CSV & JSON RAG Ingestion**: Added robust support for `.csv` and `.json` files inside `PhoenixRAGPipeline`. CSV rows are parsed to descriptive sentences and nested JSON keys are recursively flattened.
- **Semantic Memory Compression**: Enhanced `consolidate_memories` to compress merged memories whose text exceeds 300 characters using model-based greedy summarization (or sentence-extractive fallback in untrained/mock mode).
- **Structured JSON Logging**: Created `JSONFormatter` in `ai_project/utils/logging.py` formatting logger outputs as single-line JSON records, and registered it in FastAPI startup lifespan.
- **Additional Test Suites**: Developed `test_structured_logging.py`, `test_csv_json_rag.py`, and `test_memory_compression.py` (total now 60 tests passing).

## [5.0.0] - 2026-06-22
### Added
- **Grouped-Query Attention (GQA)**: Configurable key-value head grouping support in `Attention` and `TransformerBlock` to reduce KV-caching memory footprint.
- **Simulated Weight Quantization**: INT4/INT8 linear weight scaling in `QuantizedLinear` and model-wide quantization mapping `quantize_model_weights`.
- **FastAPI /api/model/quantize**: Dynamic endpoint to execute simulated model quantization on the fly.
- **Recursive Character Chunker**: Advanced sliding-window chunking fallback with semantic splitting boundaries whitelisted inside `recursive_chunk_text`.
- **Memory Consolidation & Expiration**: Prunes old low-access entries and merges overlapping vector memories based on similarity threshold scoring in `consolidate_memories` and `expire_memories`.
- **FastAPI /api/memory/consolidate**: Dynamic endpoint to trigger vector store consolidation and expiration cleanup.
- **Auto-Quantized Checkpoint Loading**: Checks state dict keys for `"w_q"` buffers during startup lifespan, dynamically converting base transformer structures.
- **Expanded Test Coverage**: Formulated `test_gqa.py`, `test_quantization.py`, `test_recursive_rag.py`, and `test_memory_lifecycle.py` (total now 55 tests).

## [4.0.0] - 2026-06-22
### Added
- **RAG Ingestion Subsystem**: Added `PhoenixRAGPipeline` performing character-based sliding-window chunking (`chunk_size` and `chunk_overlap`) and document vector database indexing.
- **FastAPI /api/memory/upload**: Upload endpoint accepting `.txt`, `.md`, `.py` documents with strict 5MB size limits, path safety verification, and automatic cleanup.
- **Performance Monitor**: Created `PhoenixMonitor` middleware profiling API traffic and tracking LLM generation speeds (prefill latency, decode latency, generated tokens, tokens/sec throughput).
- **FastAPI /api/monitoring/metrics**: Performance analytics endpoint exposing API and LLM real-time profiles.
- **LoRA Weight Merging**: Folding of adapter weights ($B \times A \times \text{scaling}$) directly back into base parameters, unwrapping of `LoRALinear` layers into standard `nn.Linear` layers, and parameter unfreezing.
- **Expanded Test Coverage**: Formulated `test_rag.py`, `test_monitoring.py`, and `test_lora_merge.py` (total now 48 tests).

## [3.0.0] - 2026-06-22
### Added
- **LoRA Fine-Tuning**: Support for Parameter-Efficient Fine-Tuning (PEFT) using trainable rank adapters (`LoRALinear`) on attention query/key/value/output projections and SwiGLU MLP gates, freezing the base transformer model.
- **Multi-Agent Orchestrator**: Implemented planning, execution, and verification self-healing agent loop (`Planner` -> `Executor` -> `QA` -> `Verifier` -> `Debugger`).
- **Orchestration API Endpoint**: Added `/api/agent/orchestrate` endpoint for multi-agent task execution.
- **Coding Benchmarks**: Lightweight benchmark runner (`PhoenixBenchmarkRunner`) containing coding assertion tasks.
- **Benchmarks API Endpoint**: Added `/api/evaluate/benchmarks` POST endpoint.
- **Docker Integration**: Added `Dockerfile.backend` for FastAPI server, multi-stage `Dockerfile.frontend` using Nginx for React, and `docker-compose.yml` to orchestrate services.
- **Automated Tests**: Formulated `test_lora.py`, `test_orchestrator.py`, and `test_benchmarks.py` adding 4 new test suites (total now 43 tests).

## [2.0.0] - 2026-06-22
### Added
- **Path Safety Utility**: Shared centralized path validation module (`resolve_safe_path`) preventing directory traversal attacks.
- **Path Safety Unit Tests**: `test_path_safety.py` (3 new tests) validating path resolution boundaries.
- **Robust Import Tests**: Added module docstring preservation and local import preservation checks.

### Changed
- **Vectorized Similarity Search**: Upgraded vector memory cosine-similarity calculations to vectorized matrix multiplication (`torch.mv`) on cached stacked tensors, removing Python loop overhead.
- **CWD-Independent Vector DB**: Resolved JSON database path relative to workspace directories instead of current working directory.
- **AST-Based Import Refactoring**: Refactored `optimize_imports` to target top-level statements only, preserving lexical scope of local/conditional imports and comment content.
- **Sandbox Hardening**: Enforced unique random filename generation (`sandbox_run_*.py`) to support multi-process concurrent code execution safely.
- **Regex Hardening**: Sandbox write-blocking regex enhanced to intercept alternative write methods (`Path.write_text`, `io.open`, `shutil.copy`).

## [1.1.0] - 2026-06-22
### Added
- **Health Check Endpoint**: New `/api/health` endpoint returning system status, model info, memory count, uptime, and version.
- **Memory Search Endpoint**: New `/api/memory/search` POST endpoint for semantic similarity search.
- **Memory Clear Endpoint**: New `/api/memory/clear` DELETE endpoint for memory management.
- **Evaluation Module**: New `PhoenixEvaluator` class with perplexity calculation and code execution success rate metrics.
- **Evaluation Endpoint**: New `/api/evaluate` POST endpoint for automated model quality assessment.
- **Toast Notifications**: Real-time feedback for all dashboard operations.
- **Memory Search UI**: Semantic search bar in the Memory tab with similarity scores.
- **System Info Panel**: Sidebar panel showing model params, device, vocab size, memory count, and uptime.
- **Security Blocklist**: Sandbox now blocks dangerous patterns (`os.system`, `subprocess`, `eval`, `exec`, `__import__`).
- **SECURITY.md**: Comprehensive security architecture documentation.
- **7 New Tests**: `test_health_api.py` (7 tests) and `test_evaluator.py` (4 tests) — total now 34 tests.

### Changed
- **CORS Hardened**: Replaced wildcard `*` CORS policy with explicit localhost origins.
- **Input Validation**: All API inputs now validated with Pydantic `Field` constraints (max lengths, ranges).
- **HTTP Status Codes**: Uninitialized subsystems now return `503` instead of `500`.
- **API Lifespan**: Replaced deprecated `@app.on_event("startup")` with modern `lifespan` context manager.
- **PyTorch AMP**: Migrated from deprecated `torch.cuda.amp` to `torch.amp` module.
- **Sandbox Hardened**: Added code size limit (64KB) and dangerous pattern blocklist.
- **UI Premium Upgrade**: Glassmorphism sidebar, animated gradient logo, grid background, glow effects, micro-animations.
- **Version Bumped**: API version updated to `1.1.0`.

### Fixed
- **Type Annotation**: Fixed `temperature` parameter type from `str` to `float` in inference engine.
- **PyTorch Deprecation**: Fixed `GradScaler` and `autocast` imports in training scripts.

## [1.0.0] - 2026-06-19
### Added
- **Interactive UI Dashboard**: React Vite application featuring Chat, Sandbox, and Vector Memory tabs.
- **Model Debug Streaming Fallback**: Graceful text streaming in the inference engine when checkpoints are empty/missing.
- **Deduplication Phase**: Integrated AST-parsing and Hash-based deduplication in the data ingestion pipeline.
- **Rotary Position Embeddings (RoPE)**: Added precomputed rotary sine/cosine tables for position encoding.
- **RMSNorm & SwiGLU**: Implemented custom root-mean-square layer normalization and gated linear activation blocks.
- **Weight-Tying**: Shared embeddings and output projection weights in model instantiation.
- **Checkpoints**: Support for checkpoint saving per epoch and early stopping parameters.
- **17 pytests**: Formulated test coverage for all backend components.
- **run_phoenix.bat**: Automated launcher utility.
- **Docs**: Formed full set of developer guides.
