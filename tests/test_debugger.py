import os
import pytest
import tempfile
from pathlib import Path

from ai_project.tokenizer.tokenizer_trainer import PhoenixTokenizer
from ai_project.models.model import PhoenixTransformer, PhoenixModelArgs
from ai_project.inference.engine import PhoenixInferenceEngine
from ai_project.memory.vector_db import PhoenixMemoryStore
from ai_project.agents.sandbox import PhoenixSandbox
from ai_project.agents.debugger import PhoenixDebuggerAgent

def test_debugger_agent_workflow():
    with tempfile.TemporaryDirectory() as tmpdir:
        # 1. Create a dummy code file to train a tokenizer
        code_file = os.path.join(tmpdir, "code.py")
        with open(code_file, "w", encoding="utf-8") as f:
            f.write("print('hello')\n")
        tokenizer = PhoenixTokenizer.train([code_file], vocab_size=100, save_dir=tmpdir)
        
        args = PhoenixModelArgs(vocab_size=100, n_layers=1, dim=32, n_heads=2, hidden_dim=64, max_seq_len=64)
        model = PhoenixTransformer(args)
        model.eval()
        
        engine = PhoenixInferenceEngine(model, tokenizer, device="cpu")
        db_path = os.path.join(tmpdir, "memory.json")
        memory = PhoenixMemoryStore(model, tokenizer, db_path=db_path, device="cpu")
        sandbox = PhoenixSandbox()
        
        # 2. Setup debugger agent
        debugger = PhoenixDebuggerAgent(engine, memory, sandbox, workspace_dir=tmpdir)
        
        # 3. Create a valid and an invalid file in workspace
        valid_file = os.path.join(tmpdir, "valid.py")
        with open(valid_file, "w", encoding="utf-8") as f:
            f.write("def test():\n    pass\n")
            
        invalid_file = os.path.join(tmpdir, "invalid.py")
        with open(invalid_file, "w", encoding="utf-8") as f:
            f.write("def test(\n    pass\n")
            
        # 4. Run scanner
        files = debugger.scan_workspace()
        assert "valid.py" in files
        assert "invalid.py" in files
        
        # 5. Check syntax
        assert debugger.check_syntax("valid.py") is None
        assert debugger.check_syntax("invalid.py") is not None
        
        # 6. Find issues
        issues = debugger.find_issues()
        assert len(issues) == 1
        assert issues[0]["file_path"] == "invalid.py"
        assert issues[0]["issue_type"] == "Syntax Error"
