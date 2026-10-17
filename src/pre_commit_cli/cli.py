from __future__ import annotations

import argparse
import sys
from pathlib import Path

from pre_commit_cli import __version__
from pre_commit_cli.libmodules.ci import write_github_ci
from pre_commit_cli.libmodules.git import init_git, install_pre_commit_hook
from pre_commit_cli.libmodules.hooks import (
    add_environments,
    create_detect_secrets_baseline,
    ensure_gitignore,
    fix_config,
    write_gitleaks_config,
    write_safe_add,
)
from pre_commit_cli.libmodules.install import find_project_local_pre_commit, pre_commit_command
from pre_commit_cli.libmodules.project import inspect_project
from pre_commit_cli.libmodules.status import doctor, list_environments, show_status
from pre_commit_cli.libmodules.utils import die, echo, run, which

DESCRIPTION = "Setup, detect and manage pre-commit hooks for common project environments."

EPILOG = """
Examples:
  ./pre-commit-cli setup
  ./pre-commit-cli setup --dir /path/to/project --python
  ./pre-commit-cli setup --no-run
  ./pre-commit-cli run
  ./pre-commit-cli safe-add -- .
  ./pre-commit-cli doctor

Files created or modified by setup:
  .pre-commit-config.yaml
  .secrets.baseline
  .gitignore
  .venv/                         Python mode
  package.json/package-lock.json  Node mode, if needed
  git-safe-add                    Optional helper for checking before git add
"""


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="pre-commit-cli",
        description=DESCRIPTION,
        epilog=EPILOG,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("command", nargs="?", help="setup, add, detect, run, doctor, status, install-hook, autoupdate, ci, list, init-git, fix-config, version")
    parser.add_argument("command_args", nargs="*", help="arguments for subcommand")
    parser.add_argument("--dir", default=".", help="project directory")
    parser.add_argument("--setup", action="store_true", help="Create base config, add security hooks and install the Git hook.")
    parser.add_argument("--add", action="append", default=[], metavar="ENV", help="Add an environment/hook set. Examples: gitleaks, python, node, django, laravel.")
    parser.add_argument("--detect", action="store_true", help="Detect project environments and add matching hooks.")
    parser.add_argument("--run", nargs="?", const="", metavar="HOOK", help="Run all hooks or one hook on all files.")
    parser.add_argument("--doctor", action="store_true", help="Check tools, files and pre-commit config validity.")
    parser.add_argument("--status", action="store_true", help="Show configured hook groups.")
    parser.add_argument("--install-hook", action="store_true", help="Install .git/hooks/pre-commit.")
    parser.add_argument("--autoupdate", action="store_true", help="Run pre-commit autoupdate.")
    parser.add_argument("--ci", choices=["github"], help="Create CI workflow.")
    parser.add_argument("--list", action="store_true", help="List available environments.")
    parser.add_argument("--init-git", action="store_true", help="Initialize Git if the directory is not a Git repository.")
    parser.add_argument("--no-install", action="store_true", help="Do not install missing pre-commit automatically.")
    parser.add_argument("--dry-run", action="store_true", help="Show intended changes without writing files.")
    parser.add_argument("--version", action="store_true", help="Show version information.")
    return parser


def setup(root: Path, no_install: bool, dry_run: bool, install_hook: bool = True) -> int:
    info = inspect_project(root)
    if not info.is_git:
        echo("Git repository missing; initializing Git.")
        init_git(info.root, dry_run=dry_run)
    add_environments(info.root, ["base", "gitleaks"], dry_run=dry_run)
    write_safe_add(info.root, dry_run=dry_run)
    cmd = pre_commit_command(info.root, no_install=no_install, dry_run=dry_run)
    if install_hook:
        install_pre_commit_hook(info.root, cmd, dry_run=dry_run)
    echo("Setup complete.")
    return 0


def detect(root: Path, no_install: bool, dry_run: bool) -> int:
    info = inspect_project(root)
    echo(f"Detected environments: {', '.join(info.detected)}")
    add_environments(info.root, info.detected, dry_run=dry_run)
    pre_commit_command(info.root, no_install=no_install, dry_run=dry_run)
    return 0


def run_hooks(root: Path, no_install: bool, dry_run: bool, hook: str | None = None) -> int:
    info = inspect_project(root)
    cmd = pre_commit_command(info.root, no_install=no_install, dry_run=dry_run)
    args = [*cmd, "run"]
    if hook:
        args.append(hook)
    args.append("--all-files")
    completed = run(args, cwd=info.root, check=False, dry_run=dry_run)
    return completed.returncode


def autoupdate(root: Path, no_install: bool, dry_run: bool) -> int:
    info = inspect_project(root)
    cmd = pre_commit_command(info.root, no_install=no_install, dry_run=dry_run)
    completed = run([*cmd, "autoupdate"], cwd=info.root, check=False, dry_run=dry_run)
    return completed.returncode


def get_install_source() -> str:
    import os
    if hasattr(sys, "oxidized"):
        return "pyoxidizer"
    elif getattr(sys, 'frozen', False):
        return "pyinstaller"
    
    argv0 = sys.argv[0] if (sys.argv and sys.argv[0] is not None) else ""
    if "SHIV_ENTRY_POINT" in os.environ or ".pyz" in argv0:
        return "shiv"
    else:
        return "source"


def version(root: Path) -> int:
    local_pc = find_project_local_pre_commit(root) or which('pre-commit') or 'missing'
    
    # ANSI color codes
    blue_bold = "\033[1;34m"
    green_bold = "\033[1;32m"
    reset = "\033[0m"
    
    cli_ver = f"{green_bold}{__version__} ({get_install_source()}){reset}"
    py_ver = f"{green_bold}{sys.version.split()[0]}{reset}"
    
    argv0 = sys.argv[0] if (sys.argv and sys.argv[0] is not None) else ""
    exe_path = Path(argv0).absolute() if argv0 else "unknown"
    
    # Format and align output
    echo(f"{blue_bold}{'pre-commit-cli:':<16}{reset} {cli_ver}")
    echo(f"{blue_bold}{'executable:':<16}{reset} {exe_path}")
    echo(f"{blue_bold}{'project:':<16}{reset} {inspect_project(root).root}")
    echo(f"{blue_bold}{'python:':<16}{reset} {py_ver}")
    echo(f"{blue_bold}{'pre-commit:':<16}{reset} {local_pc}")
    return 0


def dispatch(args: argparse.Namespace) -> int:
    root = Path(args.dir).resolve()

    if args.version:
        return version(root)
    if args.list:
        list_environments()
        return 0
    if args.init_git:
        init_git(inspect_project(root).root, dry_run=args.dry_run)
        return 0
    if args.setup:
        return setup(root, args.no_install, args.dry_run)
    if args.add:
        info = inspect_project(root)
        add_environments(info.root, args.add, dry_run=args.dry_run)
        return 0
    if args.detect:
        return detect(root, args.no_install, args.dry_run)
    if args.run is not None:
        return run_hooks(root, args.no_install, args.dry_run, args.run or None)
    if args.doctor:
        info = inspect_project(root)
        cmd = None if args.no_install else pre_commit_command(info.root, no_install=False, dry_run=args.dry_run)
        return doctor(info.root, cmd)
    if args.status:
        show_status(inspect_project(root).root)
        return 0
    if args.install_hook:
        info = inspect_project(root)
        cmd = pre_commit_command(info.root, no_install=args.no_install, dry_run=args.dry_run)
        install_pre_commit_hook(info.root, cmd, dry_run=args.dry_run)
        return 0
    if args.autoupdate:
        return autoupdate(root, args.no_install, args.dry_run)
    if args.ci:
        write_github_ci(inspect_project(root).root, dry_run=args.dry_run)
        return 0

    cmd = args.command
    cargs = args.command_args
    if not cmd:
        build_parser().print_help()
        return 0
    cmd = cmd.replace("_", "-")
    if cmd == "help":
        build_parser().print_help()
        return 0
    if cmd == "setup":
        return setup(root, args.no_install, args.dry_run)
    if cmd == "add":
        if not cargs:
            return die("add requires an environment name")
        info = inspect_project(root)
        add_environments(info.root, cargs, dry_run=args.dry_run)
        return 0
    if cmd == "detect":
        return detect(root, args.no_install, args.dry_run)
    if cmd == "run":
        return run_hooks(root, args.no_install, args.dry_run, cargs[0] if cargs else None)
    if cmd == "doctor":
        info = inspect_project(root)
        pcmd = None if args.no_install else pre_commit_command(info.root, no_install=False, dry_run=args.dry_run)
        return doctor(info.root, pcmd)
    if cmd == "status":
        show_status(inspect_project(root).root)
        return 0
    if cmd == "install-hook":
        info = inspect_project(root)
        pcmd = pre_commit_command(info.root, no_install=args.no_install, dry_run=args.dry_run)
        install_pre_commit_hook(info.root, pcmd, dry_run=args.dry_run)
        return 0
    if cmd == "autoupdate":
        return autoupdate(root, args.no_install, args.dry_run)
    if cmd == "ci":
        provider = cargs[0] if cargs else "github"
        if provider != "github":
            return die("Only github CI is supported")
        write_github_ci(inspect_project(root).root, dry_run=args.dry_run)
        return 0
    if cmd == "list":
        list_environments()
        return 0
    if cmd == "init-git":
        init_git(inspect_project(root).root, dry_run=args.dry_run)
        return 0
    if cmd in {"fix-config", "fix-gitleaks-config", "fix-shfmt-config"}:
        fix_config(inspect_project(root).root, dry_run=args.dry_run)
        return 0
    if cmd == "safe-add":
        hook_rc = run_hooks(root, args.no_install, args.dry_run)
        if hook_rc != 0:
            return hook_rc
        add_args = cargs[1:] if cargs[:1] == ["--"] else cargs
        if not add_args:
            add_args = ["."]
        return run(["git", "add", *add_args], cwd=inspect_project(root).root, check=False, dry_run=args.dry_run).returncode
    return die(f"Unknown command: {cmd}")


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return dispatch(args)
    except KeyboardInterrupt:
        return die("Interrupted", 130)
    except Exception as exc:
        return die(str(exc), 1)
