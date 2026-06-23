from pathlib import Path

def resolve_safe_path(workspace_dir: Path, rel_path: str) -> Path:
    """
    Resolves a relative path within a workspace directory and ensures it does not
    escape the workspace boundaries (preventing directory traversal attacks).
    """
    target = (workspace_dir / rel_path).resolve()
    if not target.is_relative_to(workspace_dir):
        raise PermissionError(f"Access Denied: Path '{rel_path}' is outside workspace boundaries.")
    return target
