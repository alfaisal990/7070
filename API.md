# Phoenix AI API Reference

The Phoenix AI backend runs on FastAPI (port `8000`) and serves both REST endpoints and streaming connections.

## Endpoints

### 1. Health Check
Returns system status, model information, memory count, and uptime.

- **URL**: `/api/health`
- **Method**: `GET`
- **Response**:
  ```json
  {
    "status": "online",
    "version": "1.1.0",
    "uptime_seconds": 123.4,
    "model": {
      "name": "Phoenix-54M",
      "parameters": 54000000,
      "parameters_human": "54.0M",
      "is_trained": false,
      "device": "cpu",
      "max_seq_len": 1024
    },
    "memory": { "count": 12 },
    "tokenizer": { "vocab_size": 32000 }
  }
  ```

### 2. Chat Execution (REST)
Executes the agent loop (Inference + Memory + Tool execution) synchronously and returns the final answer.

- **URL**: `/api/chat`
- **Method**: `POST`
- **Request Body**:
  ```json
  {
    "prompt": "Write a python function to compute fibonacci numbers.",
    "temperature": 0.2,
    "max_tokens": 512
  }
  ```
  - `prompt`: max 10,000 characters
  - `temperature`: 0.0–2.0
  - `max_tokens`: 1–2,048
- **Response**:
  ```json
  {
    "response": "Here is the fibonacci function: ..."
  }
  ```

### 3. Chat Streaming (SSE / Chunk stream)
Streams token generation in real-time.

- **URL**: `/api/chat/stream`
- **Method**: `GET`
- **Query Parameters**:
  - `prompt` (string): Prompt text (max 10,000 characters)
  - `temperature` (float, default `0.7`): Scaling parameter
- **Response**: Streams chunks as plain text.

### 4. Run Code (Sandbox)
Runs arbitrary python code in the subprocess-based secure Sandbox.

- **URL**: `/api/sandbox/run`
- **Method**: `POST`
- **Request Body**:
  ```json
  {
    "code": "print(2 + 2)",
    "timeout": 5.0
  }
  ```
  - `code`: max 65,536 bytes. Dangerous patterns are blocked.
  - `timeout`: 0.1–30.0 seconds
- **Response**:
  ```json
  {
    "exit_code": 0,
    "stdout": "4\n",
    "stderr": "",
    "status": "success"
  }
  ```
  Status can be: `success`, `timeout`, `error`, or `blocked` (when security patterns are detected).

### 5. Fetch Memories
Gets all recorded vector memory items stored in `memory_db.json` with embedding vectors omitted for bandwidth optimization.

- **URL**: `/api/memory`
- **Method**: `GET`
- **Response**:
  ```json
  {
    "memories": [
      {
        "text": "User: Hello\nPhoenix: Hi, how can I help?",
        "metadata": { "type": "interaction" }
      }
    ]
  }
  ```

### 6. Add Memory Manually
Inserts a new factual memory record into the semantic database.

- **URL**: `/api/memory/add`
- **Method**: `POST`
- **Request Body**:
  ```json
  {
    "text": "Phoenix AI was deployed on June 19, 2026.",
    "metadata": { "type": "manual" }
  }
  ```
  - `text`: max 5,000 characters
- **Response**:
  ```json
  {
    "status": "success"
  }
  ```

### 7. Search Memories
Performs semantic similarity search across stored memories.

- **URL**: `/api/memory/search`
- **Method**: `POST`
- **Request Body**:
  ```json
  {
    "query": "deployment date",
    "top_n": 5
  }
  ```
  - `query`: max 2,000 characters
  - `top_n`: 1–50
  - `mode`: `"dense"` (default) or `"hybrid"` (Reciprocal Rank Fusion hybrid retrieval)
- **Response**:
  ```json
  {
    "results": [
      {
        "similarity": 0.87,
        "text": "Phoenix AI was deployed on June 19, 2026.",
        "metadata": { "type": "manual" }
      }
    ]
  }
  ```

### 8. Clear All Memories
Deletes all entries from the semantic memory store.

- **URL**: `/api/memory/clear`
- **Method**: `DELETE`
- **Response**:
  ```json
  {
    "status": "success",
    "message": "All memories cleared."
  }
  ```

### 9. Model Evaluation
Runs automated model quality assessment.

- **URL**: `/api/evaluate`
- **Method**: `POST`
- **Request Body**:
  ```json
  {
    "test_text": "x = 1\ny = 2\n",
    "code_samples": ["print(1)", "x = 2 + 3"]
  }
  ```
- **Response**:
  ```json
  {
    "timestamp": "2026-06-22 04:30:00",
    "model_trained": false,
    "model_params": 54000000,
    "device": "cpu",
    "perplexity": 1234.56,
    "code_execution": {
      "total": 2,
      "success": 2,
      "failed": 0,
      "timeout": 0,
      "success_rate": 100.0,
      "details": [...]
    }
  }
  ```

### 10. Debug Scan Workspace
Scans workspace for Python files and syntax errors.

- **URL**: `/api/agent/debug/scan`
- **Method**: `GET`

### 11. Debug Auto-Repair
Proposes and applies AI-generated code fixes.

- **URL**: `/api/agent/debug/repair`
- **Method**: `POST`

### 12. Code Refactoring
Apply automated refactoring with sandbox verification.

- **URL**: `/api/agent/refactor`
- **Method**: `POST`

### 13. Agent Orchestration (v3.0)
Coordinates a multi-agent self-healing planning and execution loop to solve a complex coding task.

- **URL**: `/api/agent/orchestrate`
- **Method**: `POST`
- **Request Body**:
  ```json
  {
    "task": "Create a python script in src/calc.py that does basic math operations and run it."
  }
  ```
- **Response**:
  ```json
  {
    "status": "success",
    "history": [
      {
        "step": { "action": "write_file", "target": "src/calc.py", "description": "..." },
        "status": "success",
        "details": "..."
      }
    ]
  }
  ```

### 14. Coding Benchmarks (v3.0)
Triggers local execution of coding benchmarks (HumanEval/MBPP tasks) against the LLM, computing code synthesis accuracy metrics.

- **URL**: `/api/evaluate/benchmarks`
- **Method**: `POST`
- **Response**:
  ```json
  {
    "timestamp": "2026-06-22 05:30:00",
    "total_tasks": 4,
    "passed_tasks": 4,
    "pass_rate": 100.0,
    "average_latency_seconds": 1.25,
    "results": [...]
  }
  ```

### 15. RAG Document Ingestion (v4.0)
Accepts files (`.txt`, `.md`, `.py`) and indexes them into the vector database using sliding-window chunking.

- **URL**: `/api/memory/upload`
- **Method**: `POST`
- **Content-Type**: `multipart/form-data`
- **Request Parameters**:
  - `file` (UploadFile): The file to upload (max size 5MB, format restriction `.txt`, `.md`, `.py`, `.csv`, or `.json`).
- **Response**:
  ```json
  {
    "file_name": "readme.txt",
    "chunks_count": 5,
    "status": "success"
  }
  ```

### 16. Performance Monitoring Metrics (v4.0)
Exposes performance analytics of API requests and LLM generation stats (prefill, decode speed, and token throughput).

- **URL**: `/api/monitoring/metrics`
- **Method**: `GET`
- **Response**:
  ```json
  {
    "api": {
      "total_requests": 12,
      "active_requests": 0,
      "successful_requests": 11,
      "failed_requests": 1,
      "avg_response_latency_seconds": 0.325
    },
    "llm": {
      "sessions_count": 8,
      "total_tokens_generated": 1024,
      "avg_prefill_time_seconds": 0.05,
      "avg_decode_time_seconds": 0.85,
      "tokens_per_second": 75.5
    }
  }
  ```

### 17. Model Quantization (v5.0)
Triggers simulated low-bit (e.g. 4-bit or 8-bit) integer quantization across active model weights.

- **URL**: `/api/model/quantize`
- **Method**: `POST`
- **Request Body**:
  ```json
  {
    "bits": 4
  }
  ```
- **Response**:
  ```json
  {
    "status": "success",
    "bits": 4,
    "original_trainable_parameters": 54300000,
    "quantized_trainable_parameters": 54300000,
    "message": "Model successfully quantized to 4-bit simulation."
  }
  ```

### 18. Memory Consolidation & Expiration (v5.0)
Consolidates similar vector memory entries and prunes old inactive records.

- **URL**: `/api/memory/consolidate`
- **Method**: `POST`
- **Request Body**:
  ```json
  {
    "similarity_threshold": 0.85,
    "max_age_seconds": 86400.0,
    "min_access": 2
  }
  ```
- **Response**:
  ```json
  {
    "status": "success",
    "merged_count": 2,
    "expired_count": 1,
    "remaining_count": 10
  }
  ```
