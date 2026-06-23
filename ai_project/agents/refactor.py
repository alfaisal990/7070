import re
import ast
import logging
from typing import Dict, Any

from ai_project.agents.sandbox import PhoenixSandbox
from ai_project.inference.engine import PhoenixInferenceEngine

logger = logging.getLogger("PhoenixRefactor")

class PhoenixRefactorAgent:
    """
    Phoenix Refactoring Agent (Code Assistant Subsystem).
    Provides automated operations to optimize imports, simplify loops, and inject docstrings,
    verifying all changes via sandboxed syntax audits.
    """
    def __init__(self, engine: PhoenixInferenceEngine, sandbox: PhoenixSandbox):
        self.engine = engine
        self.sandbox = sandbox

    def _fallback_optimize_imports(self, code: str) -> str:
        """Fallback line-based import optimization for code with invalid syntax."""
        lines = code.splitlines()
        import_lines = []
        rest_lines = []
        for line in lines:
            if (line.startswith("import ") or line.startswith("from ")) and not line.startswith(" "):
                import_lines.append(line.strip())
            else:
                rest_lines.append(line)
        unique_imports = sorted(list(set(import_lines)))
        new_code = "\n".join(unique_imports) + "\n\n" + "\n".join(rest_lines)
        return new_code.strip() + "\n"

    def optimize_imports(self, code: str) -> str:
        """
        Parses, deduplicates, and sorts module-level (top-level) Python import statements.
        Preserves module docstring at the top, and leaves local imports, conditional imports,
        and strings unchanged.
        """
        try:
            tree = ast.parse(code)
        except Exception:
            # If the code has syntax errors, fall back to a safe line-based parser
            return self._fallback_optimize_imports(code)
            
        import_nodes = []
        for node in tree.body:
            if isinstance(node, (ast.Import, ast.ImportFrom)):
                import_nodes.append(node)
                
        if not import_nodes:
            return code
            
        lines = code.splitlines()
        import_lines_indices = set()
        
        for node in import_nodes:
            start = node.lineno - 1
            end = getattr(node, "end_lineno", node.lineno)
            for idx in range(start, end):
                if idx < len(lines):
                    import_lines_indices.add(idx)
                    
        # Extract and sort/deduplicate top-level imports
        extracted_imports = []
        for idx in sorted(list(import_lines_indices)):
            extracted_imports.append(lines[idx].strip())
        unique_imports = sorted(list(set(extracted_imports)))
        
        # Check for module docstring at the beginning of the file
        docstring_lines = []
        docstring_end_idx = 0
        
        if tree.body:
            first_node = tree.body[0]
            is_docstring = False
            if isinstance(first_node, ast.Expr):
                val = first_node.value
                if isinstance(val, ast.Constant) and isinstance(val.value, str):
                    is_docstring = True
                elif isinstance(val, ast.Str):
                    is_docstring = True
                    
            if is_docstring:
                end_line = getattr(first_node, "end_lineno", first_node.lineno)
                docstring_end_idx = end_line
                docstring_lines = lines[:docstring_end_idx]
                
        # Reconstruct rest of the lines (excluding docstring and imports)
        rest_lines = []
        for idx, line in enumerate(lines):
            if idx >= docstring_end_idx and idx not in import_lines_indices:
                rest_lines.append(line)
                
        # Clean up leading empty lines in rest_lines
        while rest_lines and not rest_lines[0].strip():
            rest_lines.pop(0)
            
        # Recombine
        final_parts = []
        if docstring_lines:
            final_parts.extend(docstring_lines)
            final_parts.append("")
            
        final_parts.extend(unique_imports)
        final_parts.append("")
        final_parts.extend(rest_lines)
        
        final_code = "\n".join(final_parts)
        return final_code.strip() + "\n"

    def add_docstrings(self, code: str) -> str:
        """Auto-injects placeholder docstrings into Python functions without docstrings."""
        lines = code.splitlines()
        new_lines = []
        
        for i, line in enumerate(lines):
            new_lines.append(line)
            # Find function definitions
            match = re.match(r"^(\s*)def\s+\w+\s*\(.*?\)\s*:", line)
            if match:
                indent = match.group(1) + "    "
                # Check if next line is already a docstring
                has_docstring = False
                if i + 1 < len(lines):
                    next_line = lines[i+1].strip()
                    if next_line.startswith('"""') or next_line.startswith("'''"):
                        has_docstring = True
                
                if not has_docstring:
                    new_lines.append(f'{indent}"""Auto-generated docstring."""')
                    
        return "\n".join(new_lines) + "\n"

    def refactor_code(self, code: str, refactor_type: str) -> Dict[str, Any]:
        """Applies refactoring and verifies it inside the sandbox."""
        if refactor_type == "optimize_imports":
            refactored = self.optimize_imports(code)
        elif refactor_type == "add_docstrings":
            refactored = self.add_docstrings(code)
        else:
            # Fallback/default: AI-based optimization suggestion
            prompt = (
                f"Optimize the following Python code for readability and efficiency:\n\n"
                f"```python\n{code}\n```\n\n"
                f"Provide the corrected, full python code inside <execute_code>corrected code</execute_code> tags."
            )
            response = self.engine.generate(prompt, max_new_tokens=512, temperature=0.1)
            
            # Extract
            match = re.search(r"<execute_code>([\s\S]*?)</execute_code>", response)
            if not match:
                match = re.search(r"```python\n([\s\S]*?)```", response)
            refactored = match.group(1).strip() if match else code
            
        # Verify in Sandbox
        sandbox_res = self.sandbox.execute_code(refactored)
        if sandbox_res["status"] == "success" and sandbox_res["exit_code"] == 0:
            return {
                "status": "success",
                "original": code,
                "refactored": refactored,
                "sandbox_output": sandbox_res["stdout"]
            }
        else:
            return {
                "status": "failed",
                "reason": "Refactored code failed sandbox validation.",
                "original": code,
                "refactored": refactored,
                "sandbox_output": sandbox_res["stderr"] or sandbox_res["stdout"]
            }
