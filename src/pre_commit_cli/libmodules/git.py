from __future__ import annotations

from pathlib import Path

from .utils import run, which


def init_git(root: Path, dry_run: bool = False) -> None:
    if (root / ".git").exists():
        return
    if not which("git"):
        raise RuntimeError("git is not installed or not in PATH")
    run(["git", "init"], cwd=root, dry_run=dry_run)


def install_pre_commit_hook(root: Path, pre_commit_cmd: list[str], dry_run: bool = False) -> None:
    run([*pre_commit_cmd, "install"], cwd=root, dry_run=dry_run)
