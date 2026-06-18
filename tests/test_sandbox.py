import pytest
import tempfile
from ai_project.agents.sandbox import PhoenixSandbox

def test_sandbox_success():
    sandbox = PhoenixSandbox()
    code = "print('line 1')\nprint('line 2')"
    res = sandbox.execute_code(code)
    
    assert res["status"] == "success"
    assert res["exit_code"] == 0
    assert "line 1" in res["stdout"]
    assert "line 2" in res["stdout"]
    assert res["stderr"] == ""

def test_sandbox_runtime_error():
    sandbox = PhoenixSandbox()
    code = "x = 1 / 0"
    res = sandbox.execute_code(code)
    
    assert res["status"] == "success"
    assert res["exit_code"] != 0
    assert "ZeroDivisionError" in res["stderr"]

def test_sandbox_timeout():
    sandbox = PhoenixSandbox()
    code = """
import time
while True:
    time.sleep(0.1)
"""
    res = sandbox.execute_code(code, timeout=1.0)
    
    assert res["status"] == "timeout"
    assert res["exit_code"] == -1
    assert "timed out" in res["stderr"]
