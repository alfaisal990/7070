import os
import ast
import logging
from pathlib import Path
from typing import List, Dict, Optional, Tuple

from ai_project.inference.engine import PhoenixInferenceEngine
from ai_project.memory.vector_db import PhoenixMemoryStore
from ai_project.agents.sandbox import PhoenixSandbox
from ai_project.utils.path_safety import resolve_safe_path

logger = logging.getLogger("PhoenixDebugger")

class PhoenixDebuggerAgent:
    """
    Phoenix Debugger Agent (Next Generation Proactive System).
    Scans the workspace for Python files, detects syntax errors and quality issues,
    proposes automated repairs, verifies fixes in the secure sandbox,
    and records results in vector memory.
    """
    def __init__(
        self,
        engine: PhoenixInferenceEngine,
        memory: PhoenixMemoryStore,
        sandbox: PhoenixSandbox,
        workspace_dir: str = "c:/Users/1/Desktop/7070"
    ):
        self.engine = engine
        self.memory = memory
        self.sandbox = sandbox
        self.workspace_dir = Path(workspace_dir).resolve()

    def scan_workspace(self) -> List[str]:
        """Scans the workspace recursively for Python files, excluding dependencies."""
        py_files = []
        for root, dirs, files in os.walk(self.workspace_dir):
            # Exclude build, cache, and virtual environments
            if any(p in root for p in [".venv", "__pycache__", ".git", ".pytest_cache"]):
                continue
            for file in files:
                if file.endswith(".py"):
                    full_path = Path(root) / file
                    # Relativize path for UI readability
                    rel_path = full_path.relative_to(self.workspace_dir)
                    py_files.append(str(rel_path).replace("\\", "/"))
        return py_files

    def check_syntax(self, rel_path: str) -> Optional[str]:
        """Checks if a file contains syntax errors using AST parsing. Returns error string if any."""
        try:
            full_path = resolve_safe_path(self.workspace_dir, rel_path)
            with open(full_path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
            ast.parse(content)
            return None
        except SyntaxError as e:
            return f"SyntaxError on line {e.lineno}, column {e.offset}: {e.msg}"
        except Exception as e:
            return f"File error: {str(e)}"

    def find_issues(self) -> List[Dict[str, str]]:
        """Scans workspace and returns a list of files with issues."""
        files = self.scan_workspace()
        issues = []
        for f in files:
            err = self.check_syntax(f)
            if err:
                issues.append({
                    "file_path": f,
                    "issue_type": "Syntax Error",
                    "details": err
                })
        return issues

    def propose_repair(self, rel_path: str, error_msg: str) -> Tuple[str, str]:
        """Uses the AI inference engine to plan and formulate a code repair."""
        full_path = resolve_safe_path(self.workspace_dir, rel_path)
        with open(full_path, "r", encoding="utf-8", errors="ignore") as f:
            broken_code = f.read()
            
        prompt = (
            f"Please fix the following syntax error in this Python file:\n"
            f"File: {rel_path}\n"
            f"Error: {error_msg}\n\n"
            f"Broken Code:\n```python\n{broken_code}\n```\n\n"
            f"Provide the corrected, full python code inside <execute_code>corrected code</execute_code> tags."
        )
        
        # Run prompt through the engine
        agent_response = self.engine.generate(prompt, max_new_tokens=512, temperature=0.1)
        return prompt, agent_response

    def run_auto_repair(self, rel_path: str, error_msg: str) -> Dict[str, any]:
        """Proposes, sandboxes, and commits a code repair if verified."""
        full_path = resolve_safe_path(self.workspace_dir, rel_path)
        prompt, response = self.propose_repair(rel_path, error_msg)
        
        # Extract corrected code from tags
        import re
        match = re.search(r"<execute_code>([\s\S]*?)</execute_code>", response)
        if not match:
            # Fallback for mock mode or direct text output
            match = re.search(r"```python\n([\s\S]*?)```", response)
            
        if not match:
            return {
                "status": "failed",
                "reason": "Could not extract corrected code from AI response.",
                "response": response
            }
            
        corrected_code = match.group(1).strip()
        
        # Verify in sandbox
        sandbox_res = self.sandbox.execute_code(corrected_code)
        if sandbox_res["status"] == "success" and sandbox_res["exit_code"] == 0:
            # Commit fix to file system
            try:
                with open(full_path, "w", encoding="utf-8") as f:
                    f.write(corrected_code)
                
                # Archival in vector memory
                self.memory.add_memory(
                    f"Repaired file {rel_path} containing syntax error: {error_msg}.",
                    {"type": "repair", "file_path": rel_path, "status": "success"}
                )
                
                return {
                    "status": "success",
                    "corrected_code": corrected_code,
                    "sandbox_output": sandbox_res["stdout"]
                }
            except Exception as e:
                return {
                    "status": "failed",
                    "reason": f"Failed to write file: {str(e)}",
                    "corrected_code": corrected_code
                }
        else:
            return {
                "status": "failed",
                "reason": "Sandbox verification failed.",
                "sandbox_output": sandbox_res["stderr"] or sandbox_res["stdout"],
                "corrected_code": corrected_code
            }
