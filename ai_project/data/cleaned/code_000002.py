import subprocess
import sys
import os
import tempfile
from pathlib import Path

class PhoenixSandbox:
    """
    Subprocess-based Sandbox Environment for executing Python code locally.
    Enforces process timeouts, environment isolation, and output capture.
    """
    def __init__(self, sandbox_dir: str = None):
        if sandbox_dir is None:
            self.sandbox_dir = tempfile.gettempdir()
        else:
            self.sandbox_dir = sandbox_dir
            os.makedirs(self.sandbox_dir, exist_ok=True)

    def execute_code(self, code: str, timeout: float = 5.0) -> dict:
        """
        Executes code in a Python subprocess and returns stdout, stderr, exit code, and status.
        """
        # Save code to temporary execution file
        temp_file = Path(self.sandbox_dir) / "sandbox_run.py"
        with open(temp_file, "w", encoding="utf-8") as f:
            f.write(code)
            
        # Use active virtual environment python interpreter if available
        python_exe = sys.executable or "python"
        
        # Isolate environment to limit system access
        restricted_env = {
            "PATH": os.environ.get("PATH", ""),
            "SYSTEMROOT": os.environ.get("SYSTEMROOT", ""),
            "TEMP": self.sandbox_dir,
            "TMP": self.sandbox_dir,
        }
        
        try:
            result = subprocess.run(
                [python_exe, str(temp_file)],
                capture_output=True,
                text=True,
                timeout=timeout,
                cwd=self.sandbox_dir,
                env=restricted_env
            )
            return {
                "exit_code": result.returncode,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "status": "success"
            }
        except subprocess.TimeoutExpired:
            return {
                "exit_code": -1,
                "stdout": "",
                "stderr": f"Error: Process timed out after {timeout} seconds.",
                "status": "timeout"
            }
        except Exception as e:
            return {
                "exit_code": -1,
                "stdout": "",
                "stderr": f"Execution failure: {str(e)}",
                "status": "error"
            }
        finally:
            # Clean up execution file
            if os.path.exists(temp_file):
                try:
                    os.remove(temp_file)
                except OSError:
                    pass
