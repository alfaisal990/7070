import os
import time
import uuid
import shutil
from pathlib import Path
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Request, UploadFile, File, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, JSONResponse
from pydantic import BaseModel, Field
import torch

from ai_project.models.model import PhoenixTransformer, PhoenixModelArgs
from ai_project.tokenizer.tokenizer_trainer import PhoenixTokenizer
from ai_project.inference.engine import PhoenixInferenceEngine
from ai_project.memory.vector_db import PhoenixMemoryStore
from ai_project.agents.sandbox import PhoenixSandbox
from ai_project.agents.agent import PhoenixAgent
from ai_project.agents.debugger import PhoenixDebuggerAgent
from ai_project.agents.refactor import PhoenixRefactorAgent
from ai_project.evaluation.evaluator import PhoenixEvaluator
from ai_project.agents.orchestrator import PhoenixOrchestrator
from ai_project.evaluation.benchmarks import PhoenixBenchmarkRunner
from ai_project.memory.rag import PhoenixRAGPipeline
from ai_project.api.monitoring import PhoenixMonitor
import logging
from ai_project.utils.logging import JSONFormatter
from ai_project.utils.security import is_prompt_injection
from ai_project.utils.backup import PhoenixBackupManager
from ai_project.api.config import CORS_ORIGINS
from ai_project.api.auth import (
    get_current_user, require_role, Roles,
    create_access_token, create_refresh_token, decode_jwt,
    get_user_by_username, create_user, verify_password, hash_password,
)
from ai_project.api.middleware import SecurityHeadersMiddleware, CSRFMiddleware, AuditLogMiddleware

def setup_structured_logging():
    handler = logging.StreamHandler()
    handler.setFormatter(JSONFormatter())
    
    root = logging.getLogger()
    for h in root.handlers[:]:
        root.removeHandler(h)
    root.addHandler(handler)
    root.setLevel(logging.INFO)
    
    for name in ["uvicorn", "uvicorn.error", "uvicorn.access", "fastapi", "PhoenixRAG"]:
        l = logging.getLogger(name)
        l.handlers = []
        l.propagate = True

setup_structured_logging()

# ── Constants ──────────────────────────────────────────────────
MAX_PROMPT_LENGTH = 10000
MAX_CODE_LENGTH = 65536  # 64KB
MAX_TOKENS_CAP = 2048
MAX_TIMEOUT = 30.0
STARTUP_TIME = None

class RateLimiter:
    def __init__(self, limit: int, window: float):
        self.limit = limit
        self.window = window
        self.requests = {}

    def __call__(self, request: Request):
        client_ip = request.client.host if request.client else "unknown"
        now = time.time()
        user_reqs = self.requests.setdefault(client_ip, [])
        user_reqs = [t for t in user_reqs if now - t < self.window]
        self.requests[client_ip] = user_reqs
        if len(user_reqs) >= self.limit:
            raise HTTPException(status_code=429, detail="Rate limit exceeded. Please try again later.")
        self.requests[client_ip].append(now)

chat_limiter = RateLimiter(limit=20, window=60.0)
upload_limiter = RateLimiter(limit=5, window=60.0)
sandbox_limiter = RateLimiter(limit=10, window=60.0)

# ── Global State ───────────────────────────────────────────────
tokenizer = None
model = None
engine = None
memory_store = None
sandbox = None
agent = None
debugger_agent = None
refactor_agent = None
evaluator = None
orchestrator = None
benchmark_runner = None
rag_pipeline = None
monitor = PhoenixMonitor()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Modern lifespan handler replacing deprecated @app.on_event('startup')."""
    global tokenizer, model, engine, memory_store, sandbox, agent
    global debugger_agent, refactor_agent, evaluator, orchestrator, benchmark_runner, rag_pipeline, STARTUP_TIME

    STARTUP_TIME = time.time()

    # Paths
    tokenizer_path = "ai_project/tokenizer/tokenizer.json"
    ckpt_path = "ai_project/training/checkpoints/ckpt_latest.pt"
    if not os.path.exists(ckpt_path):
        ckpt_path = "ai_project/training/sft_checkpoints/sft_latest.pt"

    # Load custom tokenizer
    print(f"API: Current working directory: {os.getcwd()}")
    print(f"API: Checking path '{tokenizer_path}': {os.path.exists(tokenizer_path)}")
    if os.path.exists(tokenizer_path):
        tokenizer = PhoenixTokenizer(tokenizer_path=tokenizer_path)
        print(f"API: Custom tokenizer loaded with vocab size {tokenizer.get_vocab_size()}.")
    else:
        tokenizer = PhoenixTokenizer()
        print(f"API: Tokenizer file not found. Initialized blank tokenizer with vocab size {tokenizer.get_vocab_size()}.")

    device = "cuda" if torch.cuda.is_available() else "cpu"

    # Load model weights if pre-trained checkpoint exists
    if os.path.exists(ckpt_path):
        print(f"API: Loading model checkpoint from {ckpt_path}")
        checkpoint = torch.load(ckpt_path, map_location=device, weights_only=False)
        model = PhoenixTransformer(checkpoint["model_args"]).to(device)
        
        # Auto-detect LoRA checkpoint and apply adapter structures
        state_dict = checkpoint["model_state"]
        is_lora = any("lora_A" in k for k in state_dict.keys())
        if is_lora:
            lora_r = checkpoint.get("lora_r", 8)
            lora_alpha = checkpoint.get("lora_alpha", 16)
            print(f"API: LoRA checkpoint detected (r={lora_r}, alpha={lora_alpha}). Applying LoRA structures...")
            from ai_project.models.model import apply_lora_to_model
            apply_lora_to_model(model, r=lora_r, alpha=lora_alpha)
            
        # Auto-detect quantized checkpoint and apply quantized structures
        is_quantized = any("w_q" in k for k in state_dict.keys())
        if is_quantized:
            bits = checkpoint.get("quantization_bits", 4)
            print(f"API: Quantized checkpoint detected (bits={bits}). Applying Quantized structures...")
            from ai_project.models.model import quantize_model_weights
            quantize_model_weights(model, bits=bits)
            
        model.load_state_dict(state_dict)
        model.is_trained = True
    else:
        print("API: No model checkpoints found. Initializing blank model.")
        args = PhoenixModelArgs()
        model = PhoenixTransformer(args).to(device)
        model.is_trained = False

    model.eval()

    # Setup submodules
    engine = PhoenixInferenceEngine(model, tokenizer, device=device)
    engine.monitor = monitor
    memory_store = PhoenixMemoryStore(model, tokenizer, device=device)
    sandbox = PhoenixSandbox()
    agent = PhoenixAgent(engine, memory_store, sandbox)
    debugger_agent = PhoenixDebuggerAgent(engine, memory_store, sandbox)
    refactor_agent = PhoenixRefactorAgent(engine, sandbox)
    evaluator = PhoenixEvaluator(model, tokenizer, sandbox, device=device)
    orchestrator = PhoenixOrchestrator(engine, memory_store, sandbox)
    benchmark_runner = PhoenixBenchmarkRunner(engine, sandbox)
    rag_pipeline = PhoenixRAGPipeline(memory_store)

    print("API: All subsystems initialized successfully.")

    yield  # Application runs

    # Cleanup on shutdown
    print("API: Shutting down Phoenix AI...")


app = FastAPI(
    title="Phoenix AI API",
    version="2.0.0",
    description="Enterprise AI coding assistant with inference, memory, sandbox, evaluation, and security capabilities."
)

# ── Security Middleware Stack (order matters: outermost first) ──
app.add_middleware(AuditLogMiddleware)
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(CSRFMiddleware)

# ── CORS — Restricted to known frontend origins ────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Re-attach lifespan to app
app.router.lifespan_context = lifespan

@app.middleware("http")
async def add_request_id_middleware(request: Request, call_next):
    request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
    from ai_project.utils.logging import request_id_context
    token = request_id_context.set(request_id)
    try:
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        return response
    finally:
        request_id_context.reset(token)

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    if exc.status_code == 500:
        error_id = str(uuid.uuid4())
        logging.exception(f"HTTP 500 Exception (Error ID: {error_id}): {exc.detail}")
        return JSONResponse(
            status_code=500,
            content={"detail": f"Internal server error. Traceback ID: {error_id}"}
        )
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
        headers=exc.headers
    )

@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    error_id = str(uuid.uuid4())
    logging.exception(f"Unhandled Exception (Error ID: {error_id})")
    return JSONResponse(
        status_code=500,
        content={"detail": f"Internal server error. Traceback ID: {error_id}"}
    )


# ══════════════════════════════════════════════════════════════════
#  Request / Response Models
# ══════════════════════════════════════════════════════════════════

class ChatRequest(BaseModel):
    prompt: str = Field(..., max_length=MAX_PROMPT_LENGTH)
    temperature: float = Field(default=0.2, ge=0.0, le=2.0)
    max_tokens: int = Field(default=512, ge=1, le=MAX_TOKENS_CAP)

class CodeRequest(BaseModel):
    code: str = Field(..., max_length=MAX_CODE_LENGTH)
    timeout: float = Field(default=5.0, ge=0.1, le=MAX_TIMEOUT)

class MemoryRequest(BaseModel):
    text: str = Field(..., max_length=5000)
    metadata: dict = None

class MemorySearchRequest(BaseModel):
    query: str = Field(..., max_length=2000)
    top_n: int = Field(default=5, ge=1, le=50)
    mode: str = Field(default="dense", pattern="^(dense|hybrid|graph_rag)$")

class OrchestrateRequest(BaseModel):
    task: str = Field(..., max_length=MAX_PROMPT_LENGTH)

class DebugRepairRequest(BaseModel):
    file_path: str
    error_msg: str

class RefactorRequest(BaseModel):
    code: str = Field(..., max_length=MAX_CODE_LENGTH)
    refactor_type: str

class EvaluateRequest(BaseModel):
    test_text: str = None
    code_samples: list[str] = None

class QuantizeRequest(BaseModel):
    bits: int = Field(default=4, ge=2, le=8)

class ConsolidateRequest(BaseModel):
    similarity_threshold: float = Field(default=0.85, ge=0.0, le=1.0)
    max_age_seconds: float = Field(default=86400.0, ge=0.0)
    min_access: int = Field(default=2, ge=0)


# ══════════════════════════════════════════════════════════════════
#  Health & System Endpoints
# ══════════════════════════════════════════════════════════════════

@app.get("/api/health")
async def health_check():
    """Returns system health status, model info, memory count, and uptime."""
    uptime = time.time() - STARTUP_TIME if STARTUP_TIME else 0
    model_params = sum(p.numel() for p in model.parameters()) if model else 0
    return {
        "status": "online",
        "version": "2.0.0",
        "uptime_seconds": round(uptime, 1),
        "model": {
            "name": "Phoenix-54M",
            "parameters": model_params,
            "parameters_human": f"{model_params / 1e6:.1f}M" if model_params > 0 else "0",
            "is_trained": getattr(model, "is_trained", False) if model else False,
            "device": str(next(model.parameters()).device) if model else "n/a",
            "max_seq_len": model.args.max_seq_len if model else 0,
        },
        "memory": {
            "count": len(memory_store.memories) if memory_store else 0,
        },
        "tokenizer": {
            "vocab_size": tokenizer.get_vocab_size() if tokenizer else 0,
        },
    }


@app.get("/api/health/liveness")
async def liveness_check():
    """Liveness check probe."""
    if STARTUP_TIME is None:
        raise HTTPException(status_code=503, detail="Service is starting up.")
    return {"status": "alive", "uptime_seconds": round(time.time() - STARTUP_TIME, 1)}


@app.get("/api/health/readiness")
async def readiness_check():
    """Readiness check probe verifying models and tokenizer are fully loaded."""
    if model is None or tokenizer is None or memory_store is None or engine is None:
        raise HTTPException(status_code=503, detail="Subsystems not fully initialized.")
    return {
        "status": "ready",
        "components": {
            "model": model is not None,
            "tokenizer": tokenizer is not None,
            "memory_store": memory_store is not None,
            "engine": engine is not None
        }
    }


# ══════════════════════════════════════════════════════════════════
#  Authentication Endpoints
# ══════════════════════════════════════════════════════════════════

class LoginRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=6, max_length=128)

class RegisterRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=6, max_length=128)
    role: str = Field(default="user", pattern="^(admin|developer|operator|user)$")

class RefreshRequest(BaseModel):
    refresh_token: str

@app.post("/api/auth/login")
async def login(req: LoginRequest):
    """Authenticate user and return JWT access + refresh tokens."""
    user = get_user_by_username(req.username)
    if not user or not verify_password(req.password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid username or password")
    access_token = create_access_token(user["id"], user["username"], user["role"])
    refresh_token = create_refresh_token(user["id"], user["username"], user["role"])
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "role": user["role"],
        "username": user["username"],
    }

@app.post("/api/auth/register")
async def register(req: RegisterRequest):
    """Register a new user account."""
    user = create_user(req.username, req.password, req.role)
    access_token = create_access_token(user["id"], user["username"], user["role"])
    refresh_token = create_refresh_token(user["id"], user["username"], user["role"])
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "role": user["role"],
        "username": user["username"],
    }

@app.post("/api/auth/refresh")
async def refresh_token(req: RefreshRequest):
    """Refresh an expired access token using a valid refresh token."""
    payload = decode_jwt(req.refresh_token)
    if payload.get("type") != "refresh":
        raise HTTPException(status_code=401, detail="Invalid token type. Provide a refresh token.")
    new_access = create_access_token(payload["sub"], payload["username"], payload["role"])
    return {
        "access_token": new_access,
        "token_type": "bearer",
    }

@app.get("/api/auth/me")
async def get_me(user: dict = Depends(get_current_user)):
    """Returns the current authenticated user info."""
    if user is None:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return {
        "user_id": user.get("sub"),
        "username": user.get("username"),
        "role": user.get("role"),
    }


# ══════════════════════════════════════════════════════════════════
#  Chat Endpoints
# ══════════════════════════════════════════════════════════════════

@app.post("/api/chat")
async def chat(req: ChatRequest, rate_limit = Depends(chat_limiter)):
    if agent is None:
        raise HTTPException(status_code=503, detail="Agent is not initialized.")
    if is_prompt_injection(req.prompt):
        raise HTTPException(status_code=400, detail="Potential prompt injection or instruction override detected.")
    t0 = time.time()
    monitor.start_request()
    try:
        response = agent.run_loop(req.prompt)
        latency = time.time() - t0
        monitor.end_request(latency, success=True)
        return {"response": response}
    except Exception as e:
        latency = time.time() - t0
        monitor.end_request(latency, success=False)
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/chat/stream")
async def chat_stream(prompt: str, temperature: float = 0.7, rate_limit = Depends(chat_limiter)):
    if engine is None:
        raise HTTPException(status_code=503, detail="Inference engine is not initialized.")
    if len(prompt) > MAX_PROMPT_LENGTH:
        raise HTTPException(status_code=400, detail=f"Prompt exceeds maximum length of {MAX_PROMPT_LENGTH} characters.")
    if is_prompt_injection(prompt):
        raise HTTPException(status_code=400, detail="Potential prompt injection or instruction override detected.")
    
    t0 = time.time()
    monitor.start_request()
    
    def event_generator():
        success = True
        try:
            for chunk in engine.generate_stream(prompt, temperature=temperature):
                yield chunk
        except Exception as e:
            success = False
            yield f"\n[Streaming Error: {str(e)}]"
        finally:
            latency = time.time() - t0
            monitor.end_request(latency, success=success)
            
    return StreamingResponse(event_generator(), media_type="text/plain")

@app.get("/api/monitoring/metrics")
async def get_metrics():
    """Returns performance and traffic metrics of the AI platform."""
    return monitor.get_metrics()

@app.get("/metrics")
async def prometheus_metrics():
    """Exposes platform and LLM performance metrics in Prometheus plain-text format."""
    lines = [
        "# HELP phoenix_api_requests_total Total number of API requests received.",
        "# TYPE phoenix_api_requests_total counter",
        f'phoenix_api_requests_total{{status="all"}} {monitor.total_requests}',
        f'phoenix_api_requests_total{{status="success"}} {monitor.successful_requests}',
        f'phoenix_api_requests_total{{status="failed"}} {monitor.failed_requests}',
        "",
        "# HELP phoenix_api_active_requests Number of currently active API requests.",
        "# TYPE phoenix_api_active_requests gauge",
        f"phoenix_api_active_requests {monitor.active_requests}",
        "",
        "# HELP phoenix_api_latency_seconds_total Accumulated response latency in seconds.",
        "# TYPE phoenix_api_latency_seconds_total counter",
        f"phoenix_api_latency_seconds_total {monitor.accumulated_latency}",
        "",
        "# HELP phoenix_llm_tokens_generated_total Total number of LLM tokens generated.",
        "# TYPE phoenix_llm_tokens_generated_total counter",
        f"phoenix_llm_tokens_generated_total {monitor.total_tokens_generated}",
        "",
        "# HELP phoenix_llm_prefill_seconds_total Accumulated LLM prefill phase latency in seconds.",
        "# TYPE phoenix_llm_prefill_seconds_total counter",
        f"phoenix_llm_prefill_seconds_total {monitor.total_prefill_time}",
        "",
        "# HELP phoenix_llm_decode_seconds_total Accumulated LLM decode phase latency in seconds.",
        "# TYPE phoenix_llm_decode_seconds_total counter",
        f"phoenix_llm_decode_seconds_total {monitor.total_decode_time}",
        "",
        "# HELP phoenix_llm_generation_sessions_total Total number of LLM generation sessions.",
        "# TYPE phoenix_llm_generation_sessions_total counter",
        f"phoenix_llm_generation_sessions_total {monitor.generation_sessions}"
    ]
    from fastapi import Response
    return Response(content="\n".join(lines) + "\n", media_type="text/plain; version=0.0.4; charset=utf-8")

@app.post("/api/memory/upload")
async def upload_document(file: UploadFile = File(...), rate_limit = Depends(upload_limiter)):
    """
    Ingests an uploaded document (.txt, .md, .py, .csv, .json) into the RAG vector memory store.
    Validates file extension and size (max 5MB) to ensure system security.
    """
    if rag_pipeline is None:
        raise HTTPException(status_code=503, detail="RAG pipeline is not initialized.")
        
    filename = file.filename
    if not filename:
        raise HTTPException(status_code=400, detail="Invalid filename.")
        
    ext = os.path.splitext(filename)[1].lower()
    if ext not in [".txt", ".md", ".py", ".csv", ".json"]:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported extension '{ext}'. Only .txt, .md, .py, .csv, and .json are permitted."
        )
        
    # Read content to check file size (5MB limit)
    try:
        content = await file.read()
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error reading file: {str(e)}")
        
    if len(content) > 5 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="File size exceeds the 5MB maximum limit.")
        
    # Decode and check for prompt injection / RAG poisoning signatures
    try:
        content_str = content.decode("utf-8", errors="ignore")
    except Exception:
        raise HTTPException(status_code=400, detail="Could not decode file content as UTF-8.")
        
    if is_prompt_injection(content_str):
        raise HTTPException(
            status_code=400,
            detail="Potential prompt injection or RAG poisoning attempt detected in file content."
        )
        
    # Set up temp folder safely inside workspace to prevent traversal
    temp_dir = Path("temp_uploads")
    temp_dir.mkdir(exist_ok=True)
    
    upload_id = str(uuid.uuid4())
    temp_subfolder = temp_dir / upload_id
    temp_subfolder.mkdir(parents=True, exist_ok=True)
    
    # Use only the safe basename of the uploaded file
    safe_name = os.path.basename(filename)
    temp_file_path = temp_subfolder / safe_name
    
    try:
        with open(temp_file_path, "wb") as f:
            f.write(content)
            
        result = rag_pipeline.ingest_file(str(temp_file_path))
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"RAG ingestion failed: {str(e)}")
    finally:
        # Cleanup
        if temp_file_path.exists():
            temp_file_path.unlink()
        if temp_subfolder.exists():
            temp_subfolder.rmdir()


# ══════════════════════════════════════════════════════════════════
#  Sandbox Endpoint
# ══════════════════════════════════════════════════════════════════

@app.post("/api/sandbox/run")
async def sandbox_run(req: CodeRequest, rate_limit = Depends(sandbox_limiter), user: dict = Depends(require_role(Roles.DEVELOPER))):
    if sandbox is None:
        raise HTTPException(status_code=503, detail="Sandbox is not initialized.")
    try:
        res = sandbox.execute_code(req.code, timeout=req.timeout)
        return res
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ══════════════════════════════════════════════════════════════════
#  Memory Endpoints
# ══════════════════════════════════════════════════════════════════

@app.get("/api/memory")
async def get_memories():
    if memory_store is None:
        raise HTTPException(status_code=503, detail="Memory store is not initialized.")
    # Return memories with embedding arrays stripped to save bandwidth
    stripped = [
        {"text": m["text"], "metadata": m["metadata"]}
        for m in memory_store.memories
    ]
    return {"memories": stripped}

@app.post("/api/memory/add")
async def add_memory(req: MemoryRequest):
    if memory_store is None:
        raise HTTPException(status_code=503, detail="Memory store is not initialized.")
    if is_prompt_injection(req.text):
        raise HTTPException(status_code=400, detail="Potential memory poisoning attempt detected.")
    try:
        memory_store.add_memory(req.text, req.metadata)
        return {"status": "success"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/memory/search")
async def search_memory(req: MemorySearchRequest):
    if memory_store is None:
        raise HTTPException(status_code=503, detail="Memory store is not initialized.")
    try:
        if req.mode == "hybrid":
            results = memory_store.search_memories_hybrid(req.query, top_n=req.top_n)
        elif req.mode == "graph_rag":
            results = memory_store.search_graph_rag(req.query, top_n=req.top_n)
        else:
            results = memory_store.search_memories(req.query, top_n=req.top_n)
        return {"results": results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/memory/clear")
async def clear_memory(user: dict = Depends(require_role(Roles.ADMIN))):
    if memory_store is None:
        raise HTTPException(status_code=503, detail="Memory store is not initialized.")
    try:
        memory_store.memories = []
        memory_store.save()
        return {"status": "success", "message": "All memories cleared."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ══════════════════════════════════════════════════════════════════
#  Debugger Endpoints
# ══════════════════════════════════════════════════════════════════

@app.get("/api/agent/debug/scan")
async def debug_scan(user: dict = Depends(require_role(Roles.DEVELOPER))):
    if debugger_agent is None:
        raise HTTPException(status_code=503, detail="Debugger agent is not initialized.")
    try:
        issues = debugger_agent.find_issues()
        files = debugger_agent.scan_workspace()
        return {"files": files, "issues": issues}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/agent/debug/repair")
async def debug_repair(req: DebugRepairRequest, user: dict = Depends(require_role(Roles.DEVELOPER))):
    if debugger_agent is None:
        raise HTTPException(status_code=503, detail="Debugger agent is not initialized.")
    try:
        res = debugger_agent.run_auto_repair(req.file_path, req.error_msg)
        return res
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ══════════════════════════════════════════════════════════════════
#  Refactor Endpoint
# ══════════════════════════════════════════════════════════════════

@app.post("/api/agent/refactor")
async def debug_refactor(req: RefactorRequest, user: dict = Depends(require_role(Roles.DEVELOPER))):
    if refactor_agent is None:
        raise HTTPException(status_code=503, detail="Refactor agent is not initialized.")
    try:
        res = refactor_agent.refactor_code(req.code, req.refactor_type)
        return res
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ══════════════════════════════════════════════════════════════════
#  Evaluation Endpoint
# ══════════════════════════════════════════════════════════════════

@app.post("/api/evaluate")
async def evaluate_model(req: EvaluateRequest):
    if evaluator is None:
        raise HTTPException(status_code=503, detail="Evaluator is not initialized.")
    try:
        report = evaluator.generate_report(
            test_text=req.test_text,
            code_samples=req.code_samples
        )
        return report
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ══════════════════════════════════════════════════════════════════
#  Orchestration Endpoint
# ══════════════════════════════════════════════════════════════════

@app.post("/api/agent/orchestrate")
async def orchestrate_task(req: OrchestrateRequest, rate_limit = Depends(chat_limiter)):
    if orchestrator is None:
        raise HTTPException(status_code=503, detail="Orchestrator is not initialized.")
    try:
        res = orchestrator.run_task(req.task)
        return res
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ══════════════════════════════════════════════════════════════════
#  Coding Benchmarks Endpoint
# ══════════════════════════════════════════════════════════════════

@app.post("/api/evaluate/benchmarks")
async def run_coding_benchmarks():
    if benchmark_runner is None:
        raise HTTPException(status_code=503, detail="Benchmark runner is not initialized.")
    try:
        report = benchmark_runner.run_all()
        return report
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ══════════════════════════════════════════════════════════════════
#  Model Quantization & Optimization Endpoint (v5.0)
# ══════════════════════════════════════════════════════════════════

@app.post("/api/model/quantize")
async def quantize_model(req: QuantizeRequest, user: dict = Depends(require_role(Roles.ADMIN))):
    """
    Quantizes the model parameters to a low-bit (e.g. 4-bit or 8-bit) simulated integer scaling representation
    to optimize memory usage and deployment throughput.
    """
    if model is None:
        raise HTTPException(status_code=503, detail="Model is not initialized.")
    try:
        from ai_project.models.model import quantize_model_weights
        orig_params = sum(p.numel() for p in model.parameters() if p.requires_grad)
        quantize_model_weights(model, bits=req.bits)
        new_params = sum(p.numel() for p in model.parameters() if p.requires_grad)
        
        # Synchronize active models inside engine and submodules
        global engine
        if engine is not None:
            engine.model = model
            
        return {
            "status": "success",
            "bits": req.bits,
            "original_trainable_parameters": orig_params,
            "quantized_trainable_parameters": new_params,
            "message": f"Model successfully quantized to {req.bits}-bit simulation."
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ══════════════════════════════════════════════════════════════════
#  Memory Consolidation & Expiration Endpoint (v5.0)
# ══════════════════════════════════════════════════════════════════

@app.post("/api/memory/consolidate")
async def consolidate_memory_store(req: ConsolidateRequest, user: dict = Depends(require_role(Roles.ADMIN))):
    """
    Consolidates similar memory blocks and prunes old inactive records
    to prevent vector similarity context pollution.
    """
    if memory_store is None:
        raise HTTPException(status_code=503, detail="Memory store is not initialized.")
    try:
        res_merge = memory_store.consolidate_memories(similarity_threshold=req.similarity_threshold)
        res_expire = memory_store.expire_memories(max_age_seconds=req.max_age_seconds, min_access=req.min_access)
        
        return {
            "status": "success",
            "merged_count": res_merge["merged_count"],
            "expired_count": res_expire["expired_count"],
            "remaining_count": res_expire["remaining_count"]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/admin/backup")
async def trigger_db_backup(user: dict = Depends(require_role(Roles.ADMIN))):
    """
    Triggers an atomic database backup, performs integrity check, and rotates backups.
    """
    try:
        db_path = "ai_project/memory/memory_db.json"
        if memory_store is not None:
            db_path = memory_store.db_path
        manager = PhoenixBackupManager(db_path=db_path)
        backup_file = manager.create_backup()
        return {"status": "success", "backup_file": backup_file}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ══════════════════════════════════════════════════════════════════
#  AI Explorer Endpoints (v6.0)
# ══════════════════════════════════════════════════════════════════

import json

class AIModelAddRequest(BaseModel):
    category_id: str = Field(..., max_length=100)
    name: str = Field(..., max_length=200)
    developer: str = Field(..., max_length=200)
    type: str = Field(..., max_length=200)
    parameters: str = Field(..., max_length=100)
    use_case: str = Field(..., max_length=1000)

AI_DATA_PATH = os.path.join(os.path.dirname(__file__), "ai_data.json")

def load_ai_data():
    if not os.path.exists(AI_DATA_PATH):
        return {"categories": []}
    with open(AI_DATA_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

def save_ai_data_atomic(data):
    temp_path = AI_DATA_PATH + ".tmp"
    with open(temp_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    os.replace(temp_path, AI_DATA_PATH)

@app.get("/api/ai_explorer/search")
async def search_ai_types(query: str = None, category_id: str = None):
    """
    Returns AI categories and filters models matching optional query and category_id.
    """
    try:
        data = load_ai_data()
        results = []
        for cat in data.get("categories", []):
            if category_id and cat["id"] != category_id:
                continue
            
            filtered_models = []
            for m in cat.get("models", []):
                if query:
                    q = query.lower()
                    match = (
                        q in m["name"].lower() or 
                        q in m["developer"].lower() or 
                        q in m["type"].lower() or 
                        q in m["use_case"].lower()
                    )
                    if not match:
                        continue
                filtered_models.append(m)
            
            results.append({
                "id": cat["id"],
                "name": cat["name"],
                "description": cat["description"],
                "models": filtered_models
            })
        return {"categories": results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/ai_explorer/add")
async def add_ai_model(req: AIModelAddRequest):
    """
    Adds a new AI model to the specified category.
    """
    try:
        data = load_ai_data()
        category = None
        for cat in data.get("categories", []):
            if cat["id"] == req.category_id:
                category = cat
                break
        
        if not category:
            raise HTTPException(status_code=404, detail=f"Category '{req.category_id}' not found.")
            
        new_model = {
            "name": req.name,
            "developer": req.developer,
            "type": req.type,
            "parameters": req.parameters,
            "use_case": req.use_case
        }
        category.setdefault("models", []).append(new_model)
        save_ai_data_atomic(data)
        return {"status": "success", "model": new_model}
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
