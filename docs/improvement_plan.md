# Phoenix AGI — Platform Improvement Plan

This document outlines the concrete engineering roadmap to bridge the architectural gaps between the Phoenix local AI platform and enterprise-grade models and deployment infrastructures.

---

## 1. Model Subsystem Optimization

### 1.1 Hardware-Accelerated Quantization
* **Goal**: Shift from simulated quantization (float multiplication of dequantized weights on the fly) to true hardware INT4/INT8/FP8 operations.
* **Roadmap**:
  1. Integrate PyTorch `torchao` (Architecture Optimization) or `bitsandbytes` dynamic quantizers to leverage Tensor Core hardware speeds.
  2. Implement a model compilation pipeline (`torch.compile`) targeting specific CUDA compute capabilities (e.g., SM 8.0+ for bfloat16 and INT8 tensor cores).
  3. Export model weights to the standard GGUF format to enable execution using high-performance C++ runtimes (`llama.cpp`).

### 1.2 Multi-GPU Parallelism (Tensor and Pipeline)
* **Goal**: Support running larger parameter configurations (e.g., 350M+ parameter models) split across multiple consumer or enterprise GPU devices.
* **Roadmap**:
  1. Use PyTorch FSDP (Fully Sharded Data Parallel) to scale training memory footprint.
  2. Implement Tensor Parallelism (TP) sharding on Attention projection matrices (ColumnParallelLinear for $W_q, W_k, W_v$, RowParallelLinear for $W_o$) using PyTorch `torch.distributed`.
  3. Integrate Pipeline Parallelism (PP) split boundaries across transformer layers using Megatron-style batch scheduling.

---

## 2. RAG & Vector Database Scaling

### 2.1 Transition to Production Vector Databases
* **Goal**: Replace the flat JSON-cached similarity search with a high-throughput, horizontally scaleable vector store.
* **Roadmap**:
  1. Integrate `sqlite3` containing SQLite-VSS extension for disk-based vector persistence.
  2. For large enterprise deployments, introduce a Docker container dependency for Milvus or Qdrant, communicating via high-performance gRPC.
  3. Implement HNSW (Hierarchical Navigable Small World) index construction to maintain sub-millisecond retrieval speeds as databases scale beyond 100,000 document chunks.

### 2.2 Relational Entity Mapping (GraphRAG)
* **Goal**: Support semantic queries requiring multi-hop reasoning by combining vectors with entity relational networks.
* **Roadmap**:
  1. Add an entity extraction agent (using LLM tool calls) that maps text chunks to entities (e.g., persons, locations, components) and relationships.
  2. Store entity graphs in SQLite or Neo4j.
  3. Implement hybrid Graph-Vector retrieval where vector search results are augmented by querying neighboring graph nodes.

---

## 3. High-Throughput Inference (Paged Attention)

### 3.1 Paged Attention & Continuous Batching
* **Goal**: Maximize concurrent API user processing capacity by eliminating KV cache fragmentation and scheduling generation requests dynamically.
* **Roadmap**:
  1. Build a virtual memory manager partitioning the KV cache into small physical page blocks.
  2. Implement Continuous Batching (iteration-level scheduling) to inject incoming chat requests into the active execution pipeline without waiting for the entire batch to complete decoding.

---

## 4. Observability & Deployment

### 4.1 Enterprise Distributed Tracing
* **Goal**: Track request lifecycles across distributed microservices (e.g., frontend, API, sandbox instances).
* **Roadmap**:
  1. Integrate OpenTelemetry instrumentation inside FastAPI.
  2. Export trace metrics (spans for database load, embeddings generation, model prefill, decoding steps) to Jaeger or Prometheus.

### 4.2 Kubernetes Orchestration
* **Goal**: Support declarative orchestration, autoscaling, and zero-downtime updates in container clusters.
* **Roadmap**:
  1. Write Helm Charts defining deployment services, ingress rules, and horizontal pod autoscalers (HPA) using custom GPU utilization metrics.
  2. Formulate blue-green and canary service templates for zero-downtime API rollouts.
