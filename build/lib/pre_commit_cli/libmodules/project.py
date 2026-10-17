from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path


@dataclass(slots=True)
class ProjectInfo:
    root: Path
    is_git: bool
    has_python: bool
    has_node: bool
    has_php: bool
    has_django: bool
    has_laravel: bool
    has_shell: bool
    has_docker: bool
    has_markdown: bool
    detected: list[str] = field(default_factory=list)


def find_project_root(start: Path) -> Path:
    current = start.resolve()
    for parent in [current, *current.parents]:
        if (parent / ".git").exists() or any((parent / name).exists() for name in ("pyproject.toml", "package.json", "composer.json")):
            return parent
    return current


def inspect_project(path: Path) -> ProjectInfo:
    root = find_project_root(path)
    
    # 1. Python detection
    has_python = any((root / name).exists() for name in ("pyproject.toml", "requirements.txt", "setup.py", "setup.cfg", "Pipfile", "poetry.lock", "tox.ini"))
    
    # 2. Node detection
    has_node = any((root / name).exists() for name in ("package.json", "pnpm-lock.yaml", "yarn.lock", "package-lock.json", "vite.config.js", "vite.config.ts"))
    
    # 3. PHP detection
    has_php = (root / "composer.json").exists()
    
    # 4. Django detection (Python framework)
    has_django = (root / "manage.py").exists() or any(root.glob("*/settings.py"))
    if not has_django:
        # Check requirements or lock files for django
        for file in ("requirements.txt", "pyproject.toml", "Pipfile"):
            p = root / file
            if p.exists():
                try:
                    if "django" in p.read_text(encoding="utf-8", errors="ignore").lower():
                        has_django = True
                        break
                except Exception:
                    pass
                    
    # 5. Laravel detection (PHP framework)
    has_laravel = (root / "artisan").exists()
    if not has_laravel and has_php:
        composer_json = root / "composer.json"
        try:
            content = composer_json.read_text(encoding="utf-8", errors="ignore").lower()
            if "laravel/framework" in content or "laravel" in content:
                has_laravel = True
        except Exception:
            pass

    # 6. Shell/Bash detection
    has_shell = (
        any(root.glob("*.sh"))
        or any(root.glob("scripts/*.sh"))
        or any(root.glob("bin/*"))
        or (root / "justfile").exists()
        or (root / "Justfile").exists()
    )
    
    # 7. Docker detection
    has_docker = any(
        (root / name).exists()
        for name in ("Dockerfile", "docker-compose.yml", "docker-compose.yaml", "compose.yml", "compose.yaml")
    )
    
    # 8. Markdown detection
    has_markdown = any(root.glob("*.md"))

    # Populate detected environment list
    detected = ["base", "gitleaks"]
    
    if has_python:
        detected.append("python")
    if has_django:
        detected.append("django")
    if has_node:
        detected.append("node")
    if has_php:
        detected.append("php")
    if has_laravel:
        detected.append("laravel")
    if has_docker:
        detected.append("docker")
    if has_shell:
        detected.append("shell")
    if has_markdown:
        detected.append("markdown")

    # Sort the detected environments for consistency, but base and gitleaks/security should be first
    # Or just keep it as base, gitleaks, followed by others in order
    detected_set = set(detected)
    ordered_detected = ["base", "gitleaks"]
    for env in ["security", "shell", "python", "node", "php", "django", "laravel", "docker", "markdown", "yaml", "json"]:
        if env in detected_set and env not in ordered_detected:
            ordered_detected.append(env)
            
    return ProjectInfo(
        root=root,
        is_git=(root / ".git").exists(),
        has_python=has_python,
        has_node=has_node,
        has_php=has_php,
        has_django=has_django,
        has_laravel=has_laravel,
        has_shell=has_shell,
        has_docker=has_docker,
        has_markdown=has_markdown,
        detected=ordered_detected,
    )
