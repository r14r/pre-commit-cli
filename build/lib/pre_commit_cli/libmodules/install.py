from __future__ import annotations

import os
import sys
from pathlib import Path

from .utils import echo, is_executable, run, which


def project_venv_python(root: Path) -> Path:
    if os.name == "nt":
        return root / ".venv" / "Scripts" / "python.exe"
    return root / ".venv" / "bin" / "python"


def project_venv_bin(root: Path, binary: str) -> Path:
    if os.name == "nt":
        return root / ".venv" / "Scripts" / f"{binary}.exe"
    return root / ".venv" / "bin" / binary


def find_project_local_pre_commit(root: Path) -> Path | None:
    """Search for a project-local pre-commit executable in common virtualenv structures."""
    relative_dirs = [
        Path(".venv/bin/pre-commit"),
        Path(".venv-pre-commit/bin/pre-commit"),
        Path(".venv/python/bin/pre-commit"),
        Path(".venv/Scripts/pre-commit.exe"),
        Path(".venv-pre-commit/Scripts/pre-commit.exe"),
        Path(".venv/python/Scripts/pre-commit.exe"),
        Path(".venv/Scripts/pre-commit"),
        Path(".venv-pre-commit/Scripts/pre-commit"),
        Path(".venv/python/Scripts/pre-commit"),
    ]
    for rel_path in relative_dirs:
        candidate = root / rel_path
        if is_executable(candidate):
            return candidate.absolute()
            
    # Glob fallback for non-standard setups
    for path in root.glob("**/.venv*/bin/pre-commit"):
        if is_executable(path):
            return path.absolute()
    for path in root.glob("**/.venv*/Scripts/pre-commit*"):
        if is_executable(path):
            return path.absolute()
            
    return None


def find_project_local_python(root: Path) -> Path | None:
    """Search for a project-local python executable in common virtualenv structures."""
    relative_dirs = [
        Path(".venv/bin/python"),
        Path(".venv-pre-commit/bin/python"),
        Path(".venv/python/bin/python"),
        Path(".venv/Scripts/python.exe"),
        Path(".venv-pre-commit/Scripts/python.exe"),
        Path(".venv/python/Scripts/python.exe"),
        Path(".venv/bin/python3"),
        Path(".venv-pre-commit/bin/python3"),
        Path(".venv/python/bin/python3"),
    ]
    for rel_path in relative_dirs:
        candidate = root / rel_path
        if candidate.exists() and (os.name == "nt" or os.access(candidate, os.X_OK)):
            return candidate.absolute()
            
    # Glob fallback for non-standard setups
    for path in root.glob("**/.venv*/bin/python*"):
        if path.exists() and (os.name == "nt" or os.access(path, os.X_OK)):
            return path.absolute()
    for path in root.glob("**/.venv*/Scripts/python*"):
        if path.exists() and (os.name == "nt" or os.access(path, os.X_OK)):
            return path.absolute()
            
    return None


def ensure_python_pre_commit(root: Path, no_install: bool = False, dry_run: bool = False) -> list[str]:
    # 1. Search for project local pre-commit executable
    local_precommit = find_project_local_pre_commit(root)
    if local_precommit:
        return [str(local_precommit)]
        
    # 2. Check if pre-commit is on PATH
    system_bin = which("pre-commit")
    if system_bin and no_install:
        return [system_bin]
        
    if no_install:
        raise RuntimeError("pre-commit not found and --no-install was used")

    # 3. Create or find Python environment
    py = find_project_local_python(root)
    if not py:
        # We need to create a venv. Let's create it at root / ".venv" by default
        venv_dir = root / ".venv"
        if os.name == "nt":
            py = venv_dir / "Scripts" / "python.exe"
        else:
            py = venv_dir / "bin" / "python"
            
        base_python = which("python3") or which("python") or sys.executable
        echo(f"Creating project virtualenv: {venv_dir}")
        run([base_python, "-m", "venv", ".venv"], cwd=root, dry_run=dry_run)
        
    # Now run pip install upgrades
    py_cmd = str(py)
    # Ensure pip is upgraded and install/upgrade packages
    run([py_cmd, "-m", "ensurepip", "--upgrade"], cwd=root, check=False, dry_run=dry_run)
    run([py_cmd, "-m", "pip", "install", "--upgrade", "pip"], cwd=root, dry_run=dry_run)
    run([py_cmd, "-m", "pip", "install", "pre-commit", "detect-secrets"], cwd=root, dry_run=dry_run)
    
    # 4. Search again for project local pre-commit binary
    local_precommit = find_project_local_pre_commit(root)
    if local_precommit:
        return [str(local_precommit)]
        
    # Fallback to standard local path
    local_bin = project_venv_bin(root, "pre-commit")
    return [str(local_bin)]


def pre_commit_command(root: Path, no_install: bool = False, dry_run: bool = False) -> list[str]:
    return ensure_python_pre_commit(root, no_install=no_install, dry_run=dry_run)
