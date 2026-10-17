from __future__ import annotations

from pathlib import Path

from .hooks import AVAILABLE_ENVIRONMENTS, CONFIG_FILE, load_config
from .project import inspect_project
from .utils import echo, run, which


def list_environments() -> None:
    echo("Available environments:")
    for env in AVAILABLE_ENVIRONMENTS:
        echo(f"  - {env}")


def show_status(root: Path) -> None:
    info = inspect_project(root)
    echo(f"Project root: {info.root}")
    echo(f"Git repository: {'yes' if info.is_git else 'no'}")
    echo(f"Detected: {', '.join(info.detected)}")
    cfg = info.root / CONFIG_FILE
    echo(f"Config: {cfg if cfg.exists() else 'missing'}")
    if cfg.exists():
        data = load_config(cfg)
        echo("Configured repos:")
        for repo in data.get("repos", []):
            echo(f"  - {repo.get('repo')} @ {repo.get('rev', 'local')}")
            for hook in repo.get("hooks", []):
                echo(f"      - {hook.get('id')}")


def doctor(root: Path, pre_commit_cmd: list[str] | None = None) -> int:
    show_status(root)
    echo("")
    echo("Tools:")
    for tool in ["git", "python3", "python", "node", "npm", "composer", "php", "pre-commit"]:
        echo(f"  {tool:12} {which(tool) or 'missing'}")
    if pre_commit_cmd:
        try:
            completed = run([*pre_commit_cmd, "validate-config"], cwd=root, check=False, capture=True)
            echo("")
            echo("pre-commit validate-config:")
            echo(completed.stdout or completed.stderr or f"exit code {completed.returncode}")
            return completed.returncode
        except Exception as exc:
            echo(f"validate-config failed: {exc}")
            return 1
    return 0
