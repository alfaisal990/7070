# Phoenix AGI — AI Stack Audit Report

## 1. Foundation Model Architecture
- **Model**: Decoder-Only Causal Transformer (54M parameters).
- **Core Optimization Blocks**:
  - **Rotary Embeddings (RoPE)**: Applied to Attention projections.
  - **Grouped-Query Attention (GQA)**: Configurable Key-Value heads to reduce KV cache size.
  - **Sliding Window Attention (SWA)**: Trims the KV cache to window bounds ($W$).
  - **SwiGLU Activation**: Implemented in FeedForward layers.

## 2. Ingestion & RAG
- **Recursive Character Chunker**: Splits texts along paragraphs, lines, and whitespace delimiters to maintain semantic cohesiveness.
- **Hybrid Retrieval**: Employs Reciprocal Rank Fusion (RRF) combining dense PyTorch vector similarity math (`torch.mv`) and sparse term BM25 indexes.
- **GraphRAG**: Augments prompt context by parsing semantic entities and relationships from text.

## 3. Dynamic Optimization
- **Quantization**: Simulated INT4/INT8 scaling is supported on linear projection layers.
- **Speculative Decoding**: Accelerates decode throughput using draft model validation.
- **PEFT (LoRA)**: Trainable adapters targeting Attention matrices.
