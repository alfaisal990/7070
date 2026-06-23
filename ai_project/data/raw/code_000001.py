import os
import re
from pathlib import Path
from ai_project.inference.engine import PhoenixInferenceEngine
from ai_project.memory.vector_db import PhoenixMemoryStore
from ai_project.agents.sandbox import PhoenixSandbox

class PhoenixAgent:
    """
    Phoenix Agent Executor.
    Combines inference, memory, and sandboxed tool-execution.
    Supports <execute_code>, <read_file>, and <write_file> tags.
    """
    def __init__(self, engine: PhoenixInferenceEngine, memory: PhoenixMemoryStore, sandbox: PhoenixSandbox, workspace_dir: str = "c:/Users/1/Desktop/7070"):
        self.engine = engine
        self.memory = memory
        self.sandbox = sandbox
        self.workspace_dir = Path(workspace_dir).resolve()

    def _resolve_safe_path(self, rel_path: str) -> Path:
        """
        Validates paths to prevent directory traversal attacks.
        Throws a PermissionError if the target lies outside the workspace directory.
        """
        # Resolve path relative to workspace
        target = (self.workspace_dir / rel_path).resolve()
        if not target.is_relative_to(self.workspace_dir):
            raise PermissionError(f"Access Denied: Path '{rel_path}' is outside workspace boundaries.")
        return target

    def run_loop(self, user_query: str, max_steps: int = 5) -> str:
        """
        Runs the agent loop. Generates code, runs it in the sandbox,
        feeds the stdout back to the context, and repeats up to max_steps.
        """
        # Retrieve context from vector memory
        memories = self.memory.search_memories(user_query, top_n=2)
        memory_context = "\n".join([f"- {m['text']}" for m in memories]) if memories else "None"
        
        system_instructions = (
            f"You are Phoenix AI, a local agent capable of coding, writing files, and running scripts.\n"
            f"Relevant memory context:\n{memory_context}\n\n"
            f"You can execute actions using these tags:\n"
            f"1. Run Python script: Wrap the code in <execute_code>your python code</execute_code>\n"
            f"2. Read file contents: Wrap the relative path in <read_file>filename</read_file>\n"
            f"3. Write file contents: Wrap contents in <write_file path=\"filename\">contents</write_file>\n"
            f"Reflect on tool results and output a final response when the task is resolved.\n"
        )
        
        conversation = f"<|system|>\n{system_instructions}\n<|user|>\n{user_query}\n<|assistant|>\n"
        
        for step in range(max_steps):
            # Generate response from model
            response = self.engine.generate(conversation, max_new_tokens=512, temperature=0.1)
            
            # Extract tags using regex
            execute_match = re.search(r"<execute_code>(.*?)</execute_code>", response, re.DOTALL)
            read_match = re.search(r"<read_file>(.*?)</read_file>", response)
            write_match = re.search(r"<write_file path=\"(.*?)\">(.*?)</write_file>", response, re.DOTALL)
            
            tool_called = False
            tool_output = ""
            
            if execute_match:
                tool_called = True
                code = execute_match.group(1).strip()
                res = self.sandbox.execute_code(code)
                tool_output = f"<execution_result>\nstdout: {res['stdout']}\nstderr: {res['stderr']}\nexit_code: {res['exit_code']}\n</execution_result>"
                
            elif read_match:
                tool_called = True
                file_path = read_match.group(1).strip()
                try:
                    target_path = self._resolve_safe_path(file_path)
                    if target_path.exists():
                        with open(target_path, "r", encoding="utf-8") as f:
                            tool_output = f"<file_content path=\"{file_path}\">\n{f.read()}\n</file_content>"
                    else:
                        tool_output = f"<file_content path=\"{file_path}\">\nError: File not found.\n</file_content>"
                except Exception as e:
                    tool_output = f"<file_content path=\"{file_path}\">\nError: {str(e)}\n</file_content>"
                    
            elif write_match:
                tool_called = True
                file_path = write_match.group(1).strip()
                content = write_match.group(2)
                try:
                    target_path = self._resolve_safe_path(file_path)
                    os.makedirs(target_path.parent, exist_ok=True)
                    with open(target_path, "w", encoding="utf-8") as f:
                        f.write(content)
                    tool_output = f"<file_status path=\"{file_path}\">\nSuccess: File written successfully.\n</file_status>"
                except Exception as e:
                    tool_output = f"<file_status path=\"{file_path}\">\nError: {str(e)}\n</file_status>"
            
            if not tool_called:
                # Store the successful run in memory
                self.memory.add_memory(
                    f"User: {user_query}\nPhoenix: {response}",
                    {"type": "interaction"}
                )
                return response
                
            # Append execution outcome back to context
            conversation += f"{response}\n<|user|>\n{tool_output}\n<|assistant|>\n"
            
        return "Error: Maximum execution steps reached without a final answer."
