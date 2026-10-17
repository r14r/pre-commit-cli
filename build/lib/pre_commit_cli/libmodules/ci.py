from __future__ import annotations

from pathlib import Path

from .utils import write_text


def write_github_ci(root: Path, dry_run: bool = False) -> None:
    content = """name: pre-commit

on:
  pull_request:
  push:
    branches: [main, master]

jobs:
  pre-commit:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.12'
      - name: Install pre-commit
        run: python -m pip install --upgrade pre-commit
      - name: Run pre-commit
        run: pre-commit run --all-files --show-diff-on-failure
"""
    write_text(root / ".github" / "workflows" / "pre-commit.yml", content, dry_run=dry_run)
