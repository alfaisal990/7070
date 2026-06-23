import pytest
import tempfile
import os
from ai_project.evaluation.benchmarks import PhoenixBenchmarkRunner, BENCHMARK_TASKS
from ai_project.agents.sandbox import PhoenixSandbox
from ai_project.models.model import PhoenixTransformer, PhoenixModelArgs
from ai_project.tokenizer.tokenizer_trainer import PhoenixTokenizer
from ai_project.inference.engine import PhoenixInferenceEngine

class MockInferenceEngine:
    def __init__(self):
        pass

    def generate(self, prompt, max_new_tokens=256, temperature=0.1):
        # Return correct solutions to make the benchmark pass
        if "fib" in prompt:
            return "<execute_code>\ndef fib(n):\n    if n <= 0: return 0\n    if n == 1: return 1\n    a, b = 0, 1\n    for _ in range(2, n + 1):\n        a, b = b, a + b\n    return b\n</execute_code>"
        elif "sort_list" in prompt:
            return "<execute_code>\ndef sort_list(lst):\n    return sorted(lst)\n</execute_code>"
        elif "reverse_string" in prompt:
            return "<execute_code>\ndef reverse_string(s):\n    return s[::-1]\n</execute_code>"
        elif "is_prime" in prompt:
            return "<execute_code>\ndef is_prime(n):\n    if n <= 1: return False\n    for i in range(2, int(n**0.5) + 1):\n        if n % i == 0: return False\n    return True\n</execute_code>"
        return ""

def test_benchmark_runner_success():
    with tempfile.TemporaryDirectory() as tmpdir:
        sandbox = PhoenixSandbox(sandbox_dir=tmpdir)
        engine = MockInferenceEngine()
        
        runner = PhoenixBenchmarkRunner(engine, sandbox)
        
        # Test a single task
        task = BENCHMARK_TASKS[0]
        res = runner.run_benchmark_task(task)
        assert res["success"] == True
        assert res["id"] == "HumanEval_0"
        
        # Run all
        report = runner.run_all()
        assert report["passed_tasks"] == len(BENCHMARK_TASKS)
        assert report["pass_rate"] == 100.0
