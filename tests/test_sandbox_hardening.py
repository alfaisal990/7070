from ai_project.agents.sandbox import PhoenixSandbox

def test_sandbox_hardening_blocking():
    sandbox = PhoenixSandbox()
    
    # 1. Clean code execution should succeed
    res_ok = sandbox.execute_code("print(1 + 1)")
    assert res_ok["status"] == "success"
    assert "2" in res_ok["stdout"]
    
    # 2. Blocked pattern: getattr
    res_getattr = sandbox.execute_code("x = getattr(int, 'mro')")
    assert res_getattr["status"] == "blocked"
    assert "Security Error" in res_getattr["stderr"]
    
    # 3. Blocked pattern: __builtins__
    res_builtins = sandbox.execute_code("x = __builtins__")
    assert res_builtins["status"] == "blocked"
    assert "Security Error" in res_builtins["stderr"]
    
    # 4. Blocked pattern: eval / exec
    res_eval = sandbox.execute_code("eval('1+1')")
    assert res_eval["status"] == "blocked"
    assert "Security Error" in res_eval["stderr"]
    
    # 5. Path isolation: attempting to execute an external tool not in PATH (like git or node)
    # Inside sandbox, let's try running a subprocess call to look for git/node.
    # Note: subprocess itself is blocked, so that will get caught, which is also correct!
    res_sub = sandbox.execute_code("import subprocess; subprocess.run(['git'])")
    assert res_sub["status"] == "blocked"
