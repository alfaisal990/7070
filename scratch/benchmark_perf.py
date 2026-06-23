import time
import torch
import json
import os
from fastapi.testclient import TestClient
import ai_project.api.main as api_module
from ai_project.api.main import app

def benchmark_inference():
    print("--- Benchmarking Inference Engine ---")
    model = api_module.model
    tokenizer = api_module.tokenizer
    engine = api_module.engine
    
    if model is None or tokenizer is None or engine is None:
        print("Inference components not initialized. Skipping.")
        return None

    prompt = "def fibonacci(n):"
    
    # Measure generation speed
    tokens = []
    t_start = time.time()
    count = 0
    for chunk in engine.generate_stream(prompt, max_new_tokens=50, temperature=0.7):
        tokens.append(chunk)
        count += 1
    t_end = time.time()
    
    total_time = t_end - t_start
    tps = len(tokens) / total_time if total_time > 0 else 0
    print(f"Prompt: '{prompt}'")
    print(f"Tokens Generated: {len(tokens)}")
    print(f"Total Time: {total_time:.3f} s")
    print(f"Throughput: {tps:.2f} tokens/second\n")
    return {"tokens": len(tokens), "time_sec": total_time, "tokens_per_sec": tps}

def benchmark_memory():
    print("--- Benchmarking Memory Search ---")
    memory_store = api_module.memory_store
    if memory_store is None:
        print("Memory store not initialized. Skipping.")
        return None

    # Insert test data if empty
    if len(memory_store.memories) == 0:
        print("Adding sample data for memory search...")
        memory_store.add_memory("Python uses list comprehension to build lists quickly.", {"type": "test"})
        memory_store.add_memory("FastAPI is a modern web framework for building APIs with Python.", {"type": "test"})
        memory_store.add_memory("PyTorch is an open-source machine learning library based on the Torch library.", {"type": "test"})
        memory_store.add_memory("Transformers are state-of-the-art model architectures for deep learning.", {"type": "test"})
        memory_store.add_memory("Docker enables developers to package applications into containers.", {"type": "test"})

    queries = ["Python web framework", "Deep learning models", "Containerized applications"]
    
    # Dense Cosine Search
    t_start = time.time()
    for q in queries:
        memory_store.search_memories(q, top_n=3)
    dense_time = (time.time() - t_start) / len(queries) * 1000  # ms
    
    # Hybrid Search
    t_start = time.time()
    for q in queries:
        memory_store.search_memories_hybrid(q, top_n=3)
    hybrid_time = (time.time() - t_start) / len(queries) * 1000  # ms

    # Graph RAG Search
    t_start = time.time()
    for q in queries:
        memory_store.search_graph_rag(q, top_n=3)
    graph_time = (time.time() - t_start) / len(queries) * 1000  # ms

    print(f"Memory count: {len(memory_store.memories)}")
    print(f"Dense Search Latency: {dense_time:.2f} ms")
    print(f"Hybrid Search Latency: {hybrid_time:.2f} ms")
    print(f"Graph RAG Search Latency: {graph_time:.2f} ms\n")
    return {"dense_ms": dense_time, "hybrid_ms": hybrid_time, "graph_ms": graph_time}

def benchmark_api_endpoints():
    print("--- Benchmarking API Latency ---")
    client = TestClient(app)
    
    # Endpoint /api/health
    t0 = time.time()
    res = client.get("/api/health")
    health_latency = (time.time() - t0) * 1000
    print(f"GET /api/health: {health_latency:.2f} ms (Status: {res.status_code})")

    # Endpoint /metrics
    t0 = time.time()
    res = client.get("/metrics")
    metrics_latency = (time.time() - t0) * 1000
    print(f"GET /metrics: {metrics_latency:.2f} ms (Status: {res.status_code})")

    # Endpoint /api/memory
    t0 = time.time()
    res = client.get("/api/memory")
    mem_get_latency = (time.time() - t0) * 1000
    print(f"GET /api/memory: {mem_get_latency:.2f} ms (Status: {res.status_code})")

    # Endpoint /api/sandbox/run
    code = "print(sum(range(100)))"
    t0 = time.time()
    res = client.post("/api/sandbox/run", json={"code": code, "timeout": 5.0})
    sandbox_latency = (time.time() - t0) * 1000
    print(f"POST /api/sandbox/run: {sandbox_latency:.2f} ms (Status: {res.status_code})")
    
    return {
        "health_ms": health_latency,
        "metrics_ms": metrics_latency,
        "memory_get_ms": mem_get_latency,
        "sandbox_ms": sandbox_latency
    }

def main():
    # Force lifespan startup to initialize global variables in main.py
    with TestClient(app) as client:
        print("Phoenix AI Performance Benchmarking Tool\n")
        inf_res = benchmark_inference()
        mem_res = benchmark_memory()
        api_res = benchmark_api_endpoints()
        
        report = {
            "inference": inf_res,
            "memory_search": mem_res,
            "api_latency": api_res
        }
        with open("scratch/perf_benchmark_results.json", "w") as f:
            json.dump(report, f, indent=2)
        print("\nResults saved to scratch/perf_benchmark_results.json")

if __name__ == "__main__":
    main()
