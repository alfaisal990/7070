# Tasks

## Completed Tasks (v1.0.0-prod)
- [x] **Data Ingestion**: Clean, normalized CRLF endings, verified syntax validation using ast.
- [x] **Deduplication**: SHA-256 hash checks to prune duplicate content.
- [x] **Tokenizer**: Byte-Level BPE tokenizer setup with vocab size 32,000 and custom special tokens.
- [x] **Transformer Model**: Decoder-only, RMSNorm, SwiGLU, RoPE, weight-tying, KV-caching.
- [x] **Training Script**: FP16 mixed precision, GradScaler, Cosine decay lr scheduler, AdamW.
- [x] **Instruction Tuning**: Loss masking for prompt tokens, dialogue wrapping template.
- [x] **Inference Engine**: Top-K/Top-P generation with KV cache step-by-step decoding.
- [x] **Semantic Vector Database**: Dot-product cosine-similarity checks on mean embeddings.
- [x] **Sandbox Execution**: Isolated subprocess env config and timeout enforcement.
- [x] **FastAPI & React Integration**: Complete dashboard linking Chat, Sandbox, and Memory.
- [x] **Unit Testing Suite**: 17 PyTest files covering all modules.
- [x] **Batch Launcher**: One-click launch scripts.

## Completed Tasks (v1.1.0)
- [x] **PyTorch Deprecation Fix**: Migrated from `torch.cuda.amp` to `torch.amp`.
- [x] **Type Annotation Fix**: Fixed `temperature` type from `str` to `float`.
- [x] **Health Check API**: `/api/health` endpoint with system info.
- [x] **Memory Search API**: `/api/memory/search` semantic search endpoint.
- [x] **Memory Clear API**: `/api/memory/clear` DELETE endpoint.
- [x] **Evaluation Module**: Perplexity + code execution metrics.
- [x] **Modern Lifespan**: Replaced deprecated `@app.on_event("startup")`.
- [x] **CORS Hardening**: Restricted to known frontend origins.
- [x] **Input Validation**: Pydantic Field constraints on all endpoints.
- [x] **Sandbox Security**: Dangerous pattern blocklist + code size limits.
- [x] **Premium UI Upgrade**: Glassmorphism, animations, system info panel.
- [x] **Toast Notifications**: Real-time operation feedback.
- [x] **Memory Search UI**: Semantic search with similarity scores.
- [x] **Security Documentation**: SECURITY.md with full threat model.
- [x] **New Tests**: 11 additional tests (34 total, all passing).
- [x] **Updated Documentation**: CHANGELOG, API, TASKS, ROADMAP.

## Completed Tasks (v2.0.0)
- [x] **Path Safety Refactoring**: Extracted path traversal validation to shared utility `resolve_safe_path`.
- [x] **Backwards Compatibility**: Added `_resolve_safe_path` wrappers on agents to keep external scripts/tests compatible.
- [x] **Vectorized Cosine Similarity**: Switched Vector DB search from a loop-based implementation to PyTorch matrix-vector multiplication (`torch.mv`) on a 2D stacked tensor cache.
- [x] **CWD-Independent File Resolution**: Dynamically resolved Vector DB JSON file relative to the active workspace.
- [x] **AST-Based Import Sorting**: Replaced naive import extraction in refactoring with modular AST node validation.
- [x] **Concurrent Sandbox Execution**: Sandbox now uses random UUIDs for temp files (`sandbox_run_*.py`), avoiding collisions during simultaneous runs.
- [x] **Sandbox Hardening**: Enforced regex blocks against alternate write functions (`Path.write_text`, `io.open`, `shutil.copy`).
- [x] **New Tests**: Formulated 5 new tests covering path safety boundary conditions, fallback import parsing, local scope preservation, and module docstrings.

## Completed Tasks (v3.0.0)
- [x] **LoRA PEFT support**: Trainable rank adapters (`LoRALinear`) on attention query/key/value/output projections and SwiGLU MLP gates, freezing the base transformer model.
- [x] **Multi-Agent Orchestrator**: Planner -> Executor -> QA -> Verifier -> Debugger self-healing agent loop.
- [x] **Benchmarks Runner**: HumanEval/MBPP-style coding benchmark suite.
- [x] **Docker Integration**: Added dockerfiles and docker-compose files.
- [x] **New Tests**: 4 new tests covering LoRA linear forward, model application, planning, and benchmarks (total 43 tests).

## Completed Tasks (v4.0.0)
- [x] **RAG Ingestion Subsystem**: Sliding-window chunker, parsing, and document vector database indexing.
- [x] **FastAPI RAG upload**: File uploads with strict size (max 5MB) and safety validations.
- [x] **Performance Monitor**: Profiling API requests and LLM generation stats (prefill, decode latency, tokens/sec).
- [x] **LoRA Weight Merging**: Folding rank adapters back into base weights, unwrapping modules, and parameter unfreezing.
- [x] **New Tests**: 5 new tests covering RAG chunking, ingestion, performance monitoring, and LoRA merging (total 48 tests).

## Completed Tasks (v5.0.0)
- [x] **Grouped-Query Attention (GQA)**: Configurable key-value head grouping support in `Attention` and `TransformerBlock` to reduce KV-caching memory footprint.
- [x] **Simulated Weight Quantization**: INT4/INT8 linear weight scaling in `QuantizedLinear` and model-wide quantization mapping `quantize_model_weights`.
- [x] **FastAPI /api/model/quantize**: Dynamic endpoint to execute simulated model quantization on the fly.
- [x] **Recursive Character Chunker**: Advanced sliding-window chunking fallback with semantic splitting boundaries whitelisted inside `recursive_chunk_text`.
- [x] **Memory Consolidation & Expiration**: Prunes old low-access entries and merges overlapping vector memories based on similarity threshold scoring in `consolidate_memories` and `expire_memories`.
- [x] **FastAPI /api/memory/consolidate**: Dynamic endpoint to trigger vector store consolidation and expiration cleanup.
- [x] **Auto-Quantized Checkpoint Loading**: Checks state dict keys for `"w_q"` buffers during startup lifespan, dynamically converting base transformer structures.
- [x] **New Tests**: Formulated `test_gqa.py`, `test_quantization.py`, `test_recursive_rag.py`, and `test_memory_lifecycle.py` (total now 55 tests).

## Completed Tasks (v7.0.0)
- [x] **Sliding Window Attention**: Added sliding-window attention bounds in Attention layer masking and dynamically trimmed KV-cache sizes in `model.py`.
- [x] **Speculative Decoding**: Implemented token proposal generation and parallel base validation in `engine.py`.
- [x] **Hybrid Search RAG**: Created sparse BM25 tf-idf word indexer and Reciprocal Rank Fusion (RRF) combiners in `vector_db.py`.
- [x] **Observability Tracing**: Integrated `X-Request-ID` tracing middleware and propagated IDs into structured JSON outputs in `main.py` and `logging.py`.
- [x] **New Tests**: Formulated `test_sliding_window_attention.py`, `test_speculative_decoding.py`, and `test_hybrid_search.py` (total now 64 tests passing).

## Completed Tasks (v6.0.0)
- [x] **Phase 1 Reports**: Generated architecture, technical debt, security, performance, and missing features reports in the `docs/` folder.
- [x] **CSV & JSON RAG Ingestion**: Integrated CSV row parsing and JSON recursive flattening.
- [x] **Semantic Memory Compression**: Merged similar memories exceeding 300 characters are summarized automatically.
- [x] **Structured JSON Logging**: Created `JSONFormatter` and registered it in FastAPI lifespan.
- [x] **New Tests**: Formulated `test_structured_logging.py`, `test_csv_json_rag.py`, and `test_memory_compression.py` (total now 60 tests passing).

## Backlog / Planned
- [ ] Implement PyTorch DDP for training.
- [ ] Add Docker integration for Sandbox.
- [ ] Expand tokenizer vocabulary or train on broader datasets.
- [ ] RLHF / DPO alignment pipeline.
