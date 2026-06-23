import pytest
import tempfile
import os
from unittest.mock import MagicMock
from ai_project.agents.orchestrator import PhoenixOrchestrator
from ai_project.agents.sandbox import PhoenixSandbox
from ai_project.memory.vector_db import PhoenixMemoryStore
from ai_project.models.model import PhoenixTransformer, PhoenixModelArgs
from ai_project.tokenizer.tokenizer_trainer import PhoenixTokenizer
from ai_project.inference.engine import PhoenixInferenceEngine

class MockEngine:
    def __init__(self, plan_response, code_response=""):
        self.plan_response = plan_response
        self.code_response = code_response
        self.call_count = 0

    def generate(self, prompt, max_new_tokens=512, temperature=0.7):
        self.call_count += 1
        if "Planner" in prompt:
            return self.plan_response
        return self.code_response

def test_orchestrator_planning():
    # Setup dummy planner output
    mock_plan = (
        "[STEP] action: write_file | target: src/test.py | desc: write hello world\n"
        "[STEP] action: execute_code | target: src/test.py | desc: run hello world\n"
    )
    engine = MockEngine(mock_plan)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create minimal tokenizer & model
        code_file = os.path.join(tmpdir, "stub.py")
        with open(code_file, "w") as f:
            f.write("x = 1\n")
        tokenizer = PhoenixTokenizer.train([code_file], vocab_size=100, save_dir=tmpdir)
        args = PhoenixModelArgs(vocab_size=100, n_layers=1, dim=16, n_heads=2, hidden_dim=32, max_seq_len=64)
        model = PhoenixTransformer(args)
        
        memory = PhoenixMemoryStore(model, tokenizer, db_path=os.path.join(tmpdir, "mem.json"), device="cpu")
        sandbox = PhoenixSandbox(sandbox_dir=tmpdir)
        
        orch = PhoenixOrchestrator(engine, memory, sandbox, workspace_dir=tmpdir)
        
        steps = orch.plan_task("Implement hello world")
        assert len(steps) == 2
        assert steps[0]["action"] == "write_file"
        assert steps[0]["target"] == "src/test.py"
        assert steps[1]["action"] == "execute_code"
        assert steps[1]["target"] == "src/test.py"
