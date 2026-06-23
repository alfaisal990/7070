import os
import pytest
import tempfile
from pathlib import Path

from ai_project.agents.refactor import PhoenixRefactorAgent
from ai_project.agents.sandbox import PhoenixSandbox

class MockEngine:
    def __init__(self, responses=None):
        self.responses = responses or []
        self.call_count = 0

    def generate(self, prompt, max_new_tokens=512, temperature=0.7, top_k=50, top_p=0.9):
        if self.call_count < len(self.responses):
            res = self.responses[self.call_count]
            self.call_count += 1
            return res
        return ""

def test_optimize_imports():
    sandbox = PhoenixSandbox()
    agent = PhoenixRefactorAgent(engine=None, sandbox=sandbox)
    
    code = (
        "import os\n"
        "import sys\n"
        "import os\n"
        "\n"
        "def main():\n"
        "    print(os.name)\n"
    )
    
    optimized = agent.optimize_imports(code)
    # Imports should be deduplicated and sorted
    assert "import os\nimport sys" in optimized
    assert "def main():" in optimized

def test_optimize_imports_docstring_and_locals():
    sandbox = PhoenixSandbox()
    agent = PhoenixRefactorAgent(engine=None, sandbox=sandbox)
    
    code = (
        '"""\n'
        'This is a module docstring.\n'
        'It should remain at the top.\n'
        '"""\n'
        'import sys\n'
        'import os\n'
        '\n'
        'def run_process():\n'
        '    # A local import that must NOT be pulled to top-level\n'
        '    import subprocess\n'
        '    text = "import dummy"\n'
        '    print("from dummy import something")\n'
        '    return subprocess.run(["echo", "hello"])\n'
    )
    
    optimized = agent.optimize_imports(code)
    
    # Docstring must be at the very top
    assert optimized.startswith('"""\nThis is a module docstring.')
    
    # Top-level imports sorted and placed after docstring
    assert "import os\nimport sys" in optimized
    
    # Local imports preserved inside function
    assert "    import subprocess" in optimized
    
    # Fake import statements inside strings/comments preserved
    assert 'text = "import dummy"' in optimized
    assert 'print("from dummy import something")' in optimized

def test_optimize_imports_syntax_error_fallback():
    sandbox = PhoenixSandbox()
    agent = PhoenixRefactorAgent(engine=None, sandbox=sandbox)
    
    # Syntactically invalid code with imports
    code = (
        'import os\n'
        'import sys\n'
        'def broken_function(\n'
    )
    
    optimized = agent.optimize_imports(code)
    # Deduplication and sorting should still work via fallback
    assert "import os\nimport sys" in optimized


def test_add_docstrings():
    sandbox = PhoenixSandbox()
    agent = PhoenixRefactorAgent(engine=None, sandbox=sandbox)
    
    code = (
        "def hello():\n"
        "    return 'hello'\n"
        "\n"
        "def hello_with_doc():\n"
        "    \"\"\"This already has a doc.\"\"\"\n"
        "    return 'world'\n"
    )
    
    updated = agent.add_docstrings(code)
    assert '    """Auto-generated docstring."""' in updated
    assert '    """This already has a doc."""' in updated
    # Check that we only added it for functions without docstrings
    lines = updated.splitlines()
    # Check hello def line is followed by the auto-generated docstring
    for i, line in enumerate(lines):
        if "def hello():" in line:
            assert '"""Auto-generated docstring."""' in lines[i+1]

def test_refactor_code_imports_success():
    sandbox = PhoenixSandbox()
    agent = PhoenixRefactorAgent(engine=None, sandbox=sandbox)
    
    code = (
        "import os\n"
        "import sys\n"
        "import os\n"
        "print('Imports optimized and valid')"
    )
    
    res = agent.refactor_code(code, "optimize_imports")
    assert res["status"] == "success"
    assert "import os\nimport sys" in res["refactored"]
    assert "original" in res

def test_refactor_code_imports_failure():
    # If the refactored code has syntax error, it should fail sandbox verification
    sandbox = PhoenixSandbox()
    agent = PhoenixRefactorAgent(engine=None, sandbox=sandbox)
    
    # Intentionally broken code with import
    code = (
        "import os\n"
        "import sys\n"
        "def broken(\n"
    )
    
    res = agent.refactor_code(code, "optimize_imports")
    assert res["status"] == "failed"
    assert "reason" in res

def test_refactor_code_ai_optimization():
    sandbox = PhoenixSandbox()
    # Mock engine that returns corrected code wrapped in tags
    mock_response = (
        "Here is the optimized code:\n"
        "<execute_code>\n"
        "def optimized_func():\n"
        "    return 42\n"
        "print(optimized_func())\n"
        "</execute_code>"
    )
    engine = MockEngine([mock_response])
    agent = PhoenixRefactorAgent(engine=engine, sandbox=sandbox)
    
    code = "def func():\n    return 42\nprint(func())"
    res = agent.refactor_code(code, "ai_optimization")
    
    assert res["status"] == "success"
    assert "optimized_func" in res["refactored"]
    assert engine.call_count == 1



