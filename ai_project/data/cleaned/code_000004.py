import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import torch

from ai_project.models.model import PhoenixTransformer, PhoenixModelArgs
from ai_project.tokenizer.tokenizer_trainer import PhoenixTokenizer
from ai_project.inference.engine import PhoenixInferenceEngine
from ai_project.memory.vector_db import PhoenixMemoryStore
from ai_project.agents.sandbox import PhoenixSandbox
from ai_project.agents.agent import PhoenixAgent

app = FastAPI(title="Phoenix AI API", version="1.0.0")

# Enable CORS for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global variables for model state
tokenizer = None
model = None
engine = None
memory_store = None
sandbox = None
agent = None

@app.on_event("startup")
def startup_event():
    global tokenizer, model, engine, memory_store, sandbox, agent
    
    # Paths
    tokenizer_path = "ai_project/tokenizer/tokenizer.json"
    ckpt_path = "ai_project/training/checkpoints/ckpt_latest.pt"
    if not os.path.exists(ckpt_path):
        ckpt_path = "ai_project/training/sft_checkpoints/sft_latest.pt"
        
    # Load custom tokenizer
    if os.path.exists(tokenizer_path):
        tokenizer = PhoenixTokenizer(tokenizer_path=tokenizer_path)
    else:
        tokenizer = PhoenixTokenizer()
        
    device = "cuda" if torch.cuda.is_available() else "cpu"
    
    # Load model weights if pre-trained checkpoint exists
    if os.path.exists(ckpt_path):
        print(f"API: Loading model checkpoint from {ckpt_path}")
        checkpoint = torch.load(ckpt_path, map_location=device, weights_only=False)
        model = PhoenixTransformer(checkpoint["model_args"]).to(device)
        model.load_state_dict(checkpoint["model_state"])
    else:
        print("API: No model checkpoints found. Initializing blank model.")
        args = PhoenixModelArgs()
        model = PhoenixTransformer(args).to(device)
        
    model.eval()
    
    # Setup submodules
    engine = PhoenixInferenceEngine(model, tokenizer, device=device)
    memory_store = PhoenixMemoryStore(model, tokenizer, device=device)
    sandbox = PhoenixSandbox()
    agent = PhoenixAgent(engine, memory_store, sandbox)

class ChatRequest(BaseModel):
    prompt: str
    temperature: float = 0.2
    max_tokens: int = 512

class CodeRequest(BaseModel):
    code: str
    timeout: float = 5.0

class MemoryRequest(BaseModel):
    text: str
    metadata: dict = None

@app.post("/api/chat")
async def chat(req: ChatRequest):
    if agent is None:
        raise HTTPException(status_code=500, detail="Agent is not initialized.")
    try:
        response = agent.run_loop(req.prompt)
        return {"response": response}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/chat/stream")
async def chat_stream(prompt: str, temperature: float = 0.7):
    if engine is None:
        raise HTTPException(status_code=500, detail="Inference engine is not initialized.")
    def event_generator():
        try:
            for chunk in engine.generate_stream(prompt, temperature=temperature):
                yield chunk
        except Exception as e:
            yield f"\n[Streaming Error: {str(e)}]"
    return StreamingResponse(event_generator(), media_type="text/plain")

@app.post("/api/sandbox/run")
async def sandbox_run(req: CodeRequest):
    if sandbox is None:
        raise HTTPException(status_code=500, detail="Sandbox is not initialized.")
    try:
        res = sandbox.execute_code(req.code, timeout=req.timeout)
        return res
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/memory")
async def get_memories():
    if memory_store is None:
        raise HTTPException(status_code=500, detail="Memory store is not initialized.")
    # Return memories with embedding arrays stripped to save bandwidth
    stripped = [
        {"text": m["text"], "metadata": m["metadata"]}
        for m in memory_store.memories
    ]
    return {"memories": stripped}

@app.post("/api/memory/add")
async def add_memory(req: MemoryRequest):
    if memory_store is None:
        raise HTTPException(status_code=500, detail="Memory store is not initialized.")
    try:
        memory_store.add_memory(req.text, req.metadata)
        return {"status": "success"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
