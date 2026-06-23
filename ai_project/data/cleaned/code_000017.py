import os
import pytest
import tempfile
from pathlib import Path
from ai_project.tokenizer.tokenizer_trainer import PhoenixTokenizer
from ai_project.models.model import PhoenixTransformer, PhoenixModelArgs
from ai_project.inference.engine import PhoenixInferenceEngine
from ai_project.memory.vector_db import PhoenixMemoryStore
from ai_project.agents.sandbox import PhoenixSandbox
from ai_project.agents.agent import PhoenixAgent

class MockEngine:
    def __init__(self, responses):
        self.responses = responses
        self.call_count = 0
        
    def generate(self, prompt, max_new_tokens=512, temperature=0.7, top_k=50, top_p=0.9):
        res = self.responses[self.call_count]
        self.call_count += 1
        return res

def test_agent_path_security():
    # Setup dummy dependencies
    with tempfile.TemporaryDirectory() as tmpdir:
        sandbox = PhoenixSandbox(sandbox_dir=tmpdir)
        # We don't need real model/tokenizer for path security check
        agent = PhoenixAgent(
            engine=None,
            memory=None,
            sandbox=sandbox,
            workspace_dir=tmpdir
        )
        
        # Valid path
        valid_path = agent._resolve_safe_path("src/utils.py")
        assert valid_path.is_relative_to(Path(tmpdir).resolve())
        
        # Invalid path traversal outside workspace
        with pytest.raises(PermissionError):
            agent._resolve_safe_path("../outside.py")

def test_agent_tool_loop_execution():
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create a dummy tokenizer & model
        dummy_code = "x = 1\n"
        code_file = os.path.join(tmpdir, "code.py")
        with open(code_file, "w", encoding="utf-8") as f:
            f.write(dummy_code)
        tokenizer = PhoenixTokenizer.train([code_file], vocab_size=100, save_dir=tmpdir)
        
        args = PhoenixModelArgs(vocab_size=100, n_layers=1, dim=16, n_heads=2, hidden_dim=32, max_seq_len=64)
        model = PhoenixTransformer(args)
        
        db_path = os.path.join(tmpdir, "memory.json")
        memory = PhoenixMemoryStore(model, tokenizer, db_path=db_path, device="cpu")
        sandbox = PhoenixSandbox(sandbox_dir=tmpdir)
        
        # Mock engine with a multi-step execution flow:
        # Step 1: LLM outputs an execute_code command
        # Step 2: LLM outputs a write_file command
        # Step 3: LLM outputs a final response
        responses = [
            "<execute_code>print(2+2)</execute_code>",
            "<write_file path=\"test_file.txt\">hello world</write_file>",
            "The calculation is complete and file is written. Hello!"
        ]
        mock_engine = MockEngine(responses)
        
        agent = PhoenixAgent(
            engine=mock_engine,
            memory=memory,
            sandbox=sandbox,
            workspace_dir=tmpdir
        )
        
        res = agent.run_loop("Solve task.", max_steps=4)
        
        assert mock_engine.call_count == 3
        assert "The calculation is complete" in res
        
        # Verify write_file executed successfully
        written_file = Path(tmpdir) / "test_file.txt"
        assert written_file.exists()
        with open(written_file, "r") as f:
            assert f.read() == "hello world"
            
        # Verify memory was updated
        assert len(memory.memories) == 1
        assert "Solve task" in memory.memories[0]["text"]
