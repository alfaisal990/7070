import re
import time
import logging
from typing import Dict, List, Any
from ai_project.inference.engine import PhoenixInferenceEngine
from ai_project.agents.sandbox import PhoenixSandbox

logger = logging.getLogger("PhoenixBenchmarks")

BENCHMARK_TASKS = [
    {
        "id": "HumanEval_0",
        "task_name": "Fibonacci Sequence Generator",
        "prompt": "def fib(n: int) -> int:\n    \"\"\"Return the n-th Fibonacci number.\n    fib(0) = 0, fib(1) = 1, fib(2) = 1\n    \"\"\"",
        "tests": (
            "assert fib(0) == 0\n"
            "assert fib(1) == 1\n"
            "assert fib(2) == 1\n"
            "assert fib(5) == 5\n"
            "assert fib(10) == 55\n"
        )
    },
    {
        "id": "HumanEval_1",
        "task_name": "List Sorting (Bubble Sort)",
        "prompt": "from typing import List\ndef sort_list(lst: List[int]) -> List[int]:\n    \"\"\"Sort list in ascending order.\"\"\"",
        "tests": (
            "assert sort_list([3, 1, 2]) == [1, 2, 3]\n"
            "assert sort_list([]) == []\n"
            "assert sort_list([5, 5, 5]) == [5, 5, 5]\n"
            "assert sort_list([-1, 0, -5]) == [-5, -1, 0]\n"
        )
    },
    {
        "id": "HumanEval_2",
        "task_name": "String Reversal",
        "prompt": "def reverse_string(s: str) -> str:\n    \"\"\"Reverses the input string.\"\"\"",
        "tests": (
            "assert reverse_string('hello') == 'olleh'\n"
            "assert reverse_string('') == ''\n"
            "assert reverse_string('a') == 'a'\n"
            "assert reverse_string('Phoenix') == 'xineohP'\n"
        )
    },
    {
        "id": "HumanEval_3",
        "task_name": "Is Prime",
        "prompt": "def is_prime(n: int) -> bool:\n    \"\"\"Returns True if n is prime, False otherwise.\"\"\"",
        "tests": (
            "assert is_prime(2) == True\n"
            "assert is_prime(3) == True\n"
            "assert is_prime(4) == False\n"
            "assert is_prime(11) == True\n"
            "assert is_prime(1) == False\n"
            "assert is_prime(0) == False\n"
        )
    }
]

class PhoenixBenchmarkRunner:
    """
    Coding Benchmark Suite (HumanEval/MBPP local implementation).
    Evaluates LLM coding generation capability on standard programming tasks.
    """
    def __init__(self, engine: PhoenixInferenceEngine, sandbox: PhoenixSandbox):
        self.engine = engine
        self.sandbox = sandbox

    def run_benchmark_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Runs a single benchmark task: generates solution, runs tests, and reports result."""
        prompt = (
            f"Please complete the following Python function definition. "
            f"Provide only the completed python function inside <execute_code>completed function</execute_code> tags. "
            f"Do not write other commentary.\n\n"
            f"Function:\n{task['prompt']}"
        )
        
        t0 = time.time()
        # Generate code from model
        response = self.engine.generate(prompt, max_new_tokens=256, temperature=0.1)
        latency = time.time() - t0
        
        # Extract function body
        match = re.search(r"<execute_code>([\s\S]*?)</execute_code>", response)
        if not match:
            match = re.search(r"```python\n([\s\S]*?)```", response)
            
        completed_code = match.group(1).strip() if match else response.strip()
        
        # Combine code with tests
        combined_script = f"{completed_code}\n\n# Assertion Tests:\n{task['tests']}"
        
        # Run in sandbox
        sandbox_res = self.sandbox.execute_code(combined_script)
        
        success = False
        status = sandbox_res["status"]
        exit_code = sandbox_res["exit_code"]
        
        if status == "success" and exit_code == 0:
            success = True
            
        return {
            "id": task["id"],
            "task_name": task["task_name"],
            "success": success,
            "latency_seconds": round(latency, 2),
            "generated_code": completed_code,
            "sandbox_output": sandbox_res["stdout"],
            "sandbox_error": sandbox_res["stderr"]
        }

    def run_all(self) -> Dict[str, Any]:
        """Runs all registered benchmark tasks and returns summary metrics."""
        results = []
        passed = 0
        total_latency = 0.0
        
        for task in BENCHMARK_TASKS:
            res = self.run_benchmark_task(task)
            results.append(res)
            if res["success"]:
                passed += 1
            total_latency += res["latency_seconds"]
            
        pass_rate = (passed / len(BENCHMARK_TASKS)) * 100 if BENCHMARK_TASKS else 0.0
        avg_latency = total_latency / len(BENCHMARK_TASKS) if BENCHMARK_TASKS else 0.0
        
        return {
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "total_tasks": len(BENCHMARK_TASKS),
            "passed_tasks": passed,
            "pass_rate": round(pass_rate, 1),
            "average_latency_seconds": round(avg_latency, 2),
            "results": results
        }
