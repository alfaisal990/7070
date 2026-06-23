# Security Architecture — Phoenix AI v1.1.0

This document describes the security model, threat mitigations, and hardening measures implemented in Phoenix AI.

## 1. Sandbox Isolation

The code execution sandbox uses **subprocess-based isolation** with the following protections:

### Environment Isolation
- Only essential environment variables (`PATH`, `SYSTEMROOT`, `TEMP`, `TMP`) are passed to child processes.
- `PYTHONPATH`, `HOME`, and all other variables are stripped.
- The child process runs in a sandboxed temp directory.

### Code Analysis
Before execution, all submitted code is scanned against a **blocklist of dangerous patterns**:

| Blocked Pattern | Reason |
|---|---|
| `os.system()` | Arbitrary command execution |
| `subprocess.*()` | Process spawning |
| `__import__()` | Dynamic import of dangerous modules |
| `eval()` / `exec()` | Arbitrary code evaluation |
| `shutil.rmtree()` | Recursive directory deletion |
| `os.remove()` / `os.unlink()` | File deletion |
| `open(..., 'w')` | File system writes outside sandbox |

### Resource Limits
- **Execution timeout**: Configurable (default 5s, max 30s).
- **Code size limit**: 64KB maximum.

## 2. API Security

### CORS Policy
CORS is restricted to known frontend origins:
- `http://localhost:5173` (Vite dev server)
- `http://127.0.0.1:5173` (Vite dev server)
- `http://localhost:8000` (API self-reference)
- `http://127.0.0.1:8000` (API self-reference)

**Rationale**: The previous wildcard (`*`) policy allowed any domain to make requests to the API. This restriction prevents cross-origin attacks from malicious websites.

### Input Validation
All API inputs are validated using Pydantic `Field` constraints:

| Parameter | Constraint |
|---|---|
| `prompt` | max 10,000 characters |
| `code` | max 65,536 bytes |
| `max_tokens` | 1–2,048 |
| `timeout` | 0.1–30.0 seconds |
| `temperature` | 0.0–2.0 |
| `memory text` | max 5,000 characters |
| `search query` | max 2,000 characters |

### HTTP Status Codes
- `503 Service Unavailable`: When subsystems are not initialized.
- `400 Bad Request`: When input validation fails.
- `500 Internal Server Error`: For unexpected failures.

## 3. Path Traversal Protection

The `PhoenixAgent` and `PhoenixDebuggerAgent` both implement path resolution security:

```python
def _resolve_safe_path(self, rel_path: str) -> Path:
    target = (self.workspace_dir / rel_path).resolve()
    if not target.is_relative_to(self.workspace_dir):
        raise PermissionError("Access Denied: Path is outside workspace.")
    return target
```

This prevents directory traversal attacks (e.g., `../../etc/passwd`) from accessing files outside the designated workspace.

## 4. Model Security

- **Weight-tying** ensures the model footprint stays minimal, reducing attack surface.
- **No network access**: The model runs entirely locally with no external API calls.
- **No telemetry**: No data is sent outside the local machine.

## 5. Reporting Vulnerabilities

If you discover a security vulnerability, please report it directly to the project maintainer. Do not open a public issue.
