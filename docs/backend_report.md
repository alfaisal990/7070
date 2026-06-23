# Phoenix AGI — Backend Audit Report

## 1. API Architecture
- Core framework: **FastAPI (v0.95+)** running on **Uvicorn**.
- Provides 18 endpoints spanning Chat, Sandbox, Memory, RAG, Debugger, and Quantization.
- Request correlation middleware propagates unique `X-Request-ID` across operations.

## 2. Security Controls & CORS
- **CORS Configuration**: Restricts access strictly to verified origins (`localhost` and `127.0.0.1` on ports `5173` and `8000`). Wildcard `*` in the secondary Task Manager application has been hardened to prevent browser security bypasses.
- **Input Validation**: Pydantic schema constraints with strict constraints (e.g. `max_length` and numeric range boundaries) are applied to all endpoints.
- **File Upload Security**: Enforces file size limits (<5MB), file extension checks (`.txt`, `.md`, `.py`, `.csv`, `.json`), and strips path names using `os.path.basename` to prevent traversal.

## 3. Error Handling & Exception Mapping
- Employs structured exception catching. Discloses controlled error messages in production while preserving stack traces in structured JSON server logs.
