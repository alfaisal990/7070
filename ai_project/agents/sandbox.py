"""
Phoenix AI - Docker-based Sandbox Execution
Enterprise-grade code execution with container isolation.
Falls back to subprocess sandbox when Docker is unavailable.
"""
import subprocess
import sys
import os
import re
import uuid
import logging
import json
from pathlib import Path
from typing import Optional

logger = logging.getLogger("PhoenixSandbox")

# Dangerous patterns that should be blocked in sandboxed code execution
BLOCKED_PATTERNS = [
    r"\bos\.system\s*\(",
    r"\bsubprocess\.\w+\s*\(",
    r"\b__import__\s*\(",
    r"\bshutil\.rmtree\s*\(",
    r"\bos\.remove\s*\(",
    r"\bos\.rmdir\s*\(",
    r"\bos\.unlink\s*\(",
    r"\bopen\s*\([^)]*['\"][wax\+]+",
    r"\bopen\s*\([^)]*mode\s*=\s*['\"][wax\+]+",
    r"\bio\.open\s*\([^)]*['\"][wax\+]+",
    r"\bio\.open\s*\([^)]*mode\s*=\s*['\"][wax\+]+",
    r"\b\.\s*write_text\s*\(",
    r"\b\.\s*write_bytes\s*\(",
    r"\bshutil\.(?:copy|move|copy2|copyfile|copymode|copystat)\s*\(",
    r"\b__builtins__\b",
    r"\bgetattr\b",
    r"\bsetattr\b",
    r"\bhasattr\b",
    r"\bdelattr\b",
    r"\b__dict__\b",
    r"\b__class__\b",
    r"\b__subclasses__\b",
    r"\b__getattribute__\b",
    r"\bglobals\s*\(",
    r"\blocals\s*\(",
    r"\bimportlib\b",
    r"\beval\b",
    r"\bexec\b",
]

MAX_CODE_SIZE = 65536  # 64KB

# Docker sandbox configuration
DOCKER_IMAGE = "python:3.12-slim"
DOCKER_MEMORY_LIMIT = "128m"
DOCKER_CPU_LIMIT = "0.5"
DOCKER_NETWORK = "none"  # No network access


def _is_docker_available() -> bool:
    """Check if Docker is available on the system."""
    try:
        result = subprocess.run(
            ["docker", "version", "--format", "{{.Server.Version}}"],
            capture_output=True, text=True, timeout=5
        )
        return result.returncode == 0
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False


class PhoenixSandbox:
    """
    Enterprise Sandbox Environment for executing Python code.
    Uses Docker containers when available, falls back to subprocess isolation.
    
    Docker mode provides:
    - Read-only filesystem
    - No network access
    - CPU limits (0.5 cores)
    - Memory limits (128MB)
    - Automatic container cleanup
    - Process isolation via namespaces
    
    Subprocess mode provides:
    - Environment variable stripping
    - Code pattern blocking
    - Timeout enforcement
    - Temporary file cleanup
    """
    def __init__(self, sandbox_dir: str = None, force_subprocess: bool = False):
        if sandbox_dir is None:
            import tempfile
            self.sandbox_dir = tempfile.gettempdir()
        else:
            self.sandbox_dir = sandbox_dir
            os.makedirs(self.sandbox_dir, exist_ok=True)

        self._docker_available = False if force_subprocess else _is_docker_available()
        if self._docker_available:
            logger.info("Docker sandbox mode enabled")
        else:
            logger.info("Subprocess sandbox mode (Docker not available)")

    @property
    def mode(self) -> str:
        return "docker" if self._docker_available else "subprocess"

    def _check_blocked_patterns(self, code: str) -> Optional[str]:
        """Scans code for dangerous patterns. Returns the matched pattern or None."""
        for pattern in BLOCKED_PATTERNS:
            match = re.search(pattern, code)
            if match:
                return match.group(0)
        return None

    def execute_code(self, code: str, timeout: float = 5.0) -> dict:
        """
        Executes code in an isolated environment.
        Uses Docker when available, subprocess otherwise.
        """
        # Enforce code size limit
        if len(code) > MAX_CODE_SIZE:
            return {
                "exit_code": -1,
                "stdout": "",
                "stderr": f"Error: Code exceeds maximum size limit of {MAX_CODE_SIZE} bytes.",
                "status": "error"
            }

        # Check for dangerous patterns
        blocked = self._check_blocked_patterns(code)
        if blocked:
            return {
                "exit_code": -1,
                "stdout": "",
                "stderr": f"Security Error: Blocked dangerous operation '{blocked}'. This pattern is not allowed in the sandbox.",
                "status": "blocked"
            }

        if self._docker_available:
            return self._execute_docker(code, timeout)
        else:
            return self._execute_subprocess(code, timeout)

    def _execute_docker(self, code: str, timeout: float) -> dict:
        """Execute code in a Docker container with full isolation."""
        container_name = f"phoenix-sandbox-{uuid.uuid4().hex[:12]}"

        try:
            # Run code via stdin to avoid file mounting
            cmd = [
                "docker", "run",
                "--rm",                                    # Auto-remove container
                "--name", container_name,
                "--network", DOCKER_NETWORK,               # No network
                "--memory", DOCKER_MEMORY_LIMIT,            # Memory limit
                "--cpus", DOCKER_CPU_LIMIT,                 # CPU limit
                "--read-only",                              # Read-only filesystem
                "--tmpfs", "/tmp:size=10m",                 # Small writable /tmp
                "--security-opt", "no-new-privileges",      # No privilege escalation
                "--pids-limit", "50",                        # Process limit
                "--user", "nobody",                          # Non-root user
                DOCKER_IMAGE,
                "python", "-c", code,
            ]

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=timeout + 5,  # Extra buffer for Docker overhead
            )

            return {
                "exit_code": result.returncode,
                "stdout": result.stdout[:10000],  # Limit output size
                "stderr": result.stderr[:5000],
                "status": "success",
                "sandbox_mode": "docker"
            }

        except subprocess.TimeoutExpired:
            # Kill the container if it's still running
            try:
                subprocess.run(["docker", "kill", container_name],
                             capture_output=True, timeout=5)
            except Exception:
                pass
            return {
                "exit_code": -1,
                "stdout": "",
                "stderr": f"Error: Process timed out after {timeout} seconds.",
                "status": "timeout",
                "sandbox_mode": "docker"
            }
        except Exception as e:
            return {
                "exit_code": -1,
                "stdout": "",
                "stderr": f"Docker execution failure: {str(e)}",
                "status": "error",
                "sandbox_mode": "docker"
            }

    def _execute_subprocess(self, code: str, timeout: float) -> dict:
        """Execute code in a subprocess with environment isolation (fallback)."""
        temp_file = Path(self.sandbox_dir) / f"sandbox_run_{uuid.uuid4().hex}.py"
        with open(temp_file, "w", encoding="utf-8") as f:
            f.write(code)

        python_exe = sys.executable or "python"
        python_dir = os.path.dirname(python_exe)
        system_root = os.environ.get("SYSTEMROOT", "C:\\Windows")
        system_dir = os.path.join(system_root, "System32")

        restricted_env = {
            "PATH": os.pathsep.join([python_dir, system_dir, system_root]),
            "SYSTEMROOT": system_root,
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
                "status": "success",
                "sandbox_mode": "subprocess"
            }
        except subprocess.TimeoutExpired:
            return {
                "exit_code": -1,
                "stdout": "",
                "stderr": f"Error: Process timed out after {timeout} seconds.",
                "status": "timeout",
                "sandbox_mode": "subprocess"
            }
        except Exception as e:
            return {
                "exit_code": -1,
                "stdout": "",
                "stderr": f"Execution failure: {str(e)}",
                "status": "error",
                "sandbox_mode": "subprocess"
            }
        finally:
            if os.path.exists(temp_file):
                try:
                    os.remove(temp_file)
                except OSError:
                    pass
