# Architecture Decisions

This document logs critical architectural choices made during the development of Phoenix AI.

## 1. Root Mean Square Layer Normalization (RMSNorm)
- **Decision**: Used RMSNorm instead of standard LayerNorm.
- **Rationale**: RMSNorm is computationally simpler and faster since it only scales by the root mean square without subtracting the mean. It yields similar or better training stability in decoder-only models.

## 2. Rotary Position Embeddings (RoPE)
- **Decision**: Implemented RoPE instead of static or learned absolute positional embeddings.
- **Rationale**: RoPE embeds relative position information directly into the Query-Key attention dot product, improving context length extrapolation and generalization to unseen context lengths.

## 3. SwiGLU Activation Function
- **Decision**: Replaced standard MLP/GELU with SwiGLU (Gated Linear Units using Swish activation).
- **Rationale**: SwiGLU has been shown to improve convergence rates and representation capability in Transformer models compared to standard FeedForward blocks.

## 4. Weight-Tying
- **Decision**: Shared weight matrices between the input embedding layer and the final output projection layer.
- **Rationale**: Reduces model parameter count by ~16 million parameters, lowering VRAM footprint and stabilizing model gradients on small datasets.

## 5. Local Embeddings for Vector Memory
- **Decision**: Reused the model's own token embeddings to compute vector memory vectors.
- **Rationale**: Avoids the need to boot or load an external embedding model (e.g. BERT or SentenceTransformers), reducing system footprint and memory requirements.

## 6. Subprocess-Based Code Sandbox
- **Decision**: Implemented Python subprocesses with stripped environment variables and execution timeouts for the code sandbox.
- **Rationale**: Provides a lightweight, on-device execution sandbox without the heavy dependencies of Docker or virtual machines, making local deployment on Windows 11 simple.

## 7. Shared Path Safety Utility
- **Decision**: Moved directory traversal checks from individual agent implementations into a dedicated `resolve_safe_path` utility.
- **Rationale**: Ensures the DRY (Don't Repeat Yourself) principle is maintained while establishing a central security barrier that can be easily hardened and audited in one place.

## 8. AST-Based Import Refactoring
- **Decision**: Replaced naive regex-line import extraction in the refactor agent with a comprehensive Abstract Syntax Tree (AST) parser targeting module-level `Import` and `ImportFrom` nodes only.
- **Rationale**: Prevents corruption of local or conditional imports within class and function definitions, and avoids mistaking import keywords in comments, docstrings, or string variables for actual statements.

## 9. Vectorized Cosine Similarity Search
- **Decision**: Stacked vector database embeddings into a unified 2D tensor cache and vectorized search using `torch.mv`.
- **Rationale**: Avoids Python's slow loop overhead and redundant tensor initialization steps, enabling instant retrieval over large-scale semantic vector stores.
