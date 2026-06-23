# Phoenix AI Roadmap

This document outlines the planned future milestones and release tracks for Phoenix AI.

## Version 7.0.0 - Sliding Window, Speculative Decoding, Hybrid RAG Search & Tracing ✅ (Released 2026-06-22)
- **Sliding Window Attention (SWA)**: Locally constrained causal attention table masking and KV-cache sliding boundaries.
- **Speculative Decoding**: Proposal-and-acceptance generation engine.
- **Hybrid Dense-Sparse RAG Search**: Reciprocal Rank Fusion (RRF) combining BM25 keyword match with embedding distances.
- **Observability Tracing**: Request middleware injecting `X-Request-ID` correlation identifiers into structured JSON records.
- **64 Automated Tests**: 100% pass rate.

## Version 6.0.0 - Autopilot, JSON/CSV RAG, Semantic Memory Compression & Structured Logging ✅ (Released 2026-06-22)
- **Phase 1 Reports**: Created five technical reports covering architecture, technical debt, security, performance, and missing features.
- **CSV & JSON RAG Ingestion**: Fully integrated CSV/JSON parsing and indexing support with safety whitelists.
- **Semantic Memory Compression**: Upgraded consolidate memory features to automatically summarize long memories.
- **Structured JSON Logging**: Created and integrated JSON log record formatting for all standard/uvicorn streams.
- **60 Automated Tests**: 100% pass rate.

## Version 5.0.0 - GQA, Quantization & Memory Consolidation ✅ (Released 2026-06-22)
- **Grouped-Query Attention (GQA)**: KV heads grouping implemented in attention class to reduce cache footprint.
- **Simulated Weight Quantization**: INT4/INT8 linear weight scaling in model weights.
- **FastAPI /api/model/quantize**: Dynamic model quantization trigger.
- **Recursive Character Chunker**: Injects semantic separators split whitelist for chunking.
- **Memory Consolidation & Expiration**: Tracks access counts and consolidates/expires memories automatically.
- **FastAPI /api/memory/consolidate**: Triggers database consolidation and expiration.
- **55 Automated Tests**: 100% pass rate.

## Version 4.0.0 - RAG, Monitoring & LoRA Merging ✅ (Released 2026-06-22)
- **RAG Ingestion Subsystem**: Sliding-window chunker, parsing, and document vector database indexing.
- **FastAPI RAG upload**: File uploads with strict size (max 5MB) and safety validations.
- **Performance Monitor**: Profiling API requests and LLM generation stats (prefill, decode latency, tokens/sec).
- **LoRA Weight Merging**: Folding rank adapters back into base weights, unwrapping modules, and parameter unfreezing.
- **48 Automated Tests**: 100% pass rate.

## Version 3.0.0 - Enterprise AI Ready ✅ (Released 2026-06-22)
- **LoRA PEFT support**: Integrated trainable adapter layers (`LoRALinear`) to freeze base weights and fine-tune efficiently.
- **Multi-Agent Orchestration**: Self-healing planning/execution cycle (`Planner` -> `Executor` -> `QA` -> `Verifier` -> `Debugger`).
- **Coding Benchmarks**: Formulated HumanEval/MBPP-style local suite runner (`PhoenixBenchmarkRunner`).
- **Docker Integration**: Added dockerfiles and docker-compose files for production-grade containers.
- **43 Automated Tests**: 100% pass rate.

## Version 2.0.0 - Refactored, Vectorized, Hardened ✅ (Released 2026-06-22)
- **Vectorized Search**: Cosine similarity vectorized via matrix multiplication (`torch.mv`) on a 2D tensor cache.
- **AST-Based Import Refactoring**: Modular parsing of module-level imports only, preserving docstrings and scopes.
- **CWD-Independent DB**: Dynamically resolved memories relative to the workspace.
- **Concurrency & Hardening**: Temp files UUID safety + hardened write regex blocks.

## Version 1.1.0 - Quality & Security ✅ (Released 2026-06-22)
- **Health Check API**: System status, model info, uptime monitoring.
- **Evaluation Module**: Perplexity and code execution success metrics.
- **Security Hardening**: CORS restriction, sandbox blocklist, input validation.
- **Premium UI**: Glassmorphism, animations, toast notifications, system info panel.
- **Memory Management**: Semantic search and clear endpoints.
- **PyTorch Modernization**: Migrated to `torch.amp` API.

## Future Milestones
- **Context Length Expansion**: Increase attention context limit from `1024` to `4096` tokens.
- **Model Size Scaling**: Release configurations for `125M` and `350M` parameter variants.
- **DPO Alignment**: Integrate direct preference optimization (DPO) pipelines for alignment.
- **Quantization Support**: Add FP8 / INT4 quantization utilities for ultra-low latency local deployment.
