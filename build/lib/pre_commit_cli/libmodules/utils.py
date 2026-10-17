from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Iterable, Sequence


def echo(message: str = "") -> None:
    print(message)


def warn(message: str) -> None:
    print(f"[WARN] {message}", file=sys.stderr)


def die(message: str, code: int = 1) -> int:
    print(f"[ERROR] {message}", file=sys.stderr)
    return code


def which(binary: str) -> str | None:
    return shutil.which(binary)


def run(
    cmd: Sequence[str],
    cwd: Path | None = None,
    check: bool = True,
    dry_run: bool = False,
    capture: bool = False,
) -> subprocess.CompletedProcess[str]:
    printable = " ".join(str(part) for part in cmd)
    if dry_run:
        echo(f"DRY-RUN: {printable}")
        return subprocess.CompletedProcess(list(cmd), 0, "", "")
    return subprocess.run(
        list(cmd),
        cwd=str(cwd) if cwd else None,
        check=check,
        text=True,
        stdout=subprocess.PIPE if capture else None,
        stderr=subprocess.PIPE if capture else None,
    )


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8") if path.exists() else ""


def write_text(path: Path, content: str, dry_run: bool = False) -> None:
    if dry_run:
        echo(f"DRY-RUN: write {path}")
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def append_unique_lines(path: Path, lines: Iterable[str], dry_run: bool = False) -> None:
    existing = read_text(path).splitlines()
    changed = False
    for line in lines:
        if line not in existing:
            existing.append(line)
            changed = True
    if changed or not path.exists():
        write_text(path, "\n".join(existing).rstrip() + "\n", dry_run=dry_run)


def backup_file(path: Path, dry_run: bool = False) -> Path | None:
    if not path.exists():
        return None
    idx = 1
    while True:
        backup = path.with_name(f"{path.name}.bak{idx}")
        if not backup.exists():
            break
        idx += 1
    if dry_run:
        echo(f"DRY-RUN: backup {path} -> {backup}")
        return backup
    shutil.copy2(path, backup)
    return backup


def is_executable(path: Path) -> bool:
    return path.exists() and os.access(path, os.X_OK)
