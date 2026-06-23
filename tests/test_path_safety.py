import pytest
from pathlib import Path
from ai_project.utils.path_safety import resolve_safe_path

def test_resolve_safe_path_valid():
    workspace = Path("c:/Users/1/Desktop/7070").resolve()
    
    # Simple relative path
    res = resolve_safe_path(workspace, "ai_project/agents/agent.py")
    assert res == workspace / "ai_project/agents/agent.py"
    
    # Path with redundant dots that resolve inside
    res2 = resolve_safe_path(workspace, "ai_project/../ai_project/agents/./agent.py")
    assert res2 == workspace / "ai_project/agents/agent.py"

def test_resolve_safe_path_traversal():
    workspace = Path("c:/Users/1/Desktop/7070").resolve()
    
    # Escaping via double dots
    with pytest.raises(PermissionError):
        resolve_safe_path(workspace, "../outside.txt")
        
    # Escaping via nested double dots
    with pytest.raises(PermissionError):
        resolve_safe_path(workspace, "ai_project/../../outside.txt")

def test_resolve_safe_path_absolute():
    workspace = Path("c:/Users/1/Desktop/7070").resolve()
    
    # Absolute path outside workspace
    with pytest.raises(PermissionError):
        resolve_safe_path(workspace, "c:/Windows/System32/cmd.exe")
