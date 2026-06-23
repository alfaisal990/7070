# Phoenix AGI — Missing Features Report (v7.0.0)

Gap analysis of the Phoenix AGI Platform compared to leading enterprise AI platforms (OpenAI, Claude, Llama, DeepSeek).

---

## 1. Model Subsystem Gaps
- **Mixture of Experts (MoE)**: Enterprise models utilize MoE architectures to reduce active parameters during inference. Phoenix is currently structured as a dense Transformer.
- **Flash Attention**: Lacks native CUDA Flash Attention kernels, limiting context scale processing speeds.
- **Pipeline & Tensor Parallelism**: Phoenix is restricted to single-device training/inference. It lacks multi-GPU tensor-parallel shard routing.

---

## 2. RAG & Data Subsystem Gaps
- **Complex Formats**: Lacks native PDF/DOCX binary document ingestion pipelines (requires plain-text conversions).
- **Knowledge Graphs & GraphRAG**: Similarity searches are limited to vector distance and BM25 calculations. Lacks entities relational mapping or knowledge graphs integration.

---

## 3. Observability & Infrastructure Gaps
- **Distributed Tracing**: Currently has standard correlation tracing IDs. Lacks OpenTelemetry distributed tracing middleware.
- **Kubernetes Helm Charts**: Phoenix does not contain active Kubernetes Helm charts for distributed container deployment (restricted to Docker Compose).
