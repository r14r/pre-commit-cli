from __future__ import annotations

from copy import deepcopy
from pathlib import Path
from typing import Any

import yaml

from .utils import append_unique_lines, backup_file, echo, read_text, write_text

CONFIG_FILE = ".pre-commit-config.yaml"
GITLEAKS_CONFIG_FILE = ".gitleaks.toml"

AVAILABLE_ENVIRONMENTS = [
    "base",
    "gitleaks",
    "security",
    "shell",
    "python",
    "node",
    "php",
    "django",
    "laravel",
    "docker",
    "markdown",
    "yaml",
    "json",
]

# Mapping aliases to their canonical environment name
ENV_ALIASES = {
    "base": "base",
    "secret": "gitleaks",
    "secrets": "gitleaks",
    "gitleaks": "gitleaks",
    "security": "security",
    "py": "python",
    "python": "python",
    "django": "django",
    "node": "node",
    "npm": "node",
    "js": "node",
    "javascript": "node",
    "typescript": "node",
    "ts": "node",
    "laravel": "laravel",
    "php": "php",
    "docker": "docker",
    "shell": "shell",
    "bash": "shell",
    "sh": "shell",
    "markdown": "markdown",
    "md": "markdown",
    "yaml": "yaml",
    "yml": "yaml",
    "json": "json",
}

HOOK_GROUPS: dict[str, list[dict[str, Any]]] = {
    "base": [
        {
            "repo": "https://github.com/pre-commit/pre-commit-hooks",
            "rev": "v5.0.0",
            "hooks": [
                {"id": "check-yaml"},
                {"id": "check-json"},
                {"id": "check-toml"},
                {"id": "end-of-file-fixer"},
                {"id": "trailing-whitespace"},
                {"id": "mixed-line-ending", "args": ["--fix=lf"]},
            ],
        }
    ],
    "gitleaks": [
        {
            "repo": "https://github.com/gitleaks/gitleaks",
            "rev": "v8.28.0",
            "hooks": [{"id": "gitleaks", "args": ["--config", ".gitleaks.toml"]}],
        },
        {
            "repo": "https://github.com/Yelp/detect-secrets",
            "rev": "v1.5.0",
            "hooks": [{"id": "detect-secrets", "args": ["--baseline", ".secrets.baseline"]}],
        },
    ],
    "security": [
        {
            "repo": "https://github.com/pre-commit/pre-commit-hooks",
            "rev": "v5.0.0",
            "hooks": [
                {"id": "detect-private-key"},
                {"id": "check-added-large-files", "args": ["--maxkb=1024"]},
                {"id": "check-merge-conflict"},
                {"id": "check-yaml"},
                {"id": "check-json"},
                {"id": "mixed-line-ending", "args": ["--fix=lf"]},
                {"id": "end-of-file-fixer"},
                {"id": "trailing-whitespace"},
            ],
        },
        {
            "repo": "local",
            "hooks": [
                {
                    "id": "prevent-local-env-files",
                    "name": "Prevent committing local env files",
                    "entry": "bash -c 'for file in \"$@\"; do case \"$file\" in .env|.env.*) if [ \"$file\" != \".env.example\" ] && [ \"$file\" != \".env.template\" ]; then echo \"Do not commit local secret file: $file\"; exit 1; fi;; esac; done' --",
                    "language": "system",
                    "pass_filenames": True,
                }
            ],
        },
    ],
    "shell": [
        {
            "repo": "https://github.com/scop/pre-commit-shfmt",
            "rev": "v3.12.0-2",
            "hooks": [{"id": "shfmt", "args": ["-w", "-s", "-i", "2"]}],
        },
        {
            "repo": "https://github.com/shellcheck-py/shellcheck-py",
            "rev": "v0.10.0.1",
            "hooks": [{"id": "shellcheck"}],
        },
    ],
    "python": [
        {
            "repo": "https://github.com/astral-sh/ruff-pre-commit",
            "rev": "v0.8.6",
            "hooks": [
                {"id": "ruff", "args": ["--fix"]},
                {"id": "ruff-format"},
            ],
        },
        {
            "repo": "https://github.com/pre-commit/pre-commit-hooks",
            "rev": "v5.0.0",
            "hooks": [
                {"id": "check-ast"},
                {"id": "debug-statements"},
                {"id": "name-tests-test", "args": ["--pytest-test-first"]},
            ],
        },
    ],
    "node": [
        {
            "repo": "https://github.com/pre-commit/mirrors-prettier",
            "rev": "v4.0.0-alpha.8",
            "hooks": [
                {
                    "id": "prettier",
                    "types_or": ["javascript", "jsx", "ts", "tsx", "json", "css", "scss", "markdown", "yaml"],
                }
            ],
        },
        {
            "repo": "local",
            "hooks": [
                {
                    "id": "npm-lint",
                    "name": "npm lint if configured",
                    "entry": "bash -lc 'npm run | grep -q \"lint\" && npm run lint || true'",
                    "language": "system",
                    "pass_filenames": False,
                },
                {
                    "id": "npm-test",
                    "name": "npm test if configured",
                    "entry": "bash -lc 'npm run | grep -q \"test\" && npm test || true'",
                    "language": "system",
                    "pass_filenames": False,
                },
            ],
        },
    ],
    "php": [
        {
            "repo": "local",
            "hooks": [
                {
                    "id": "composer-validate",
                    "name": "composer validate",
                    "entry": "composer validate --strict --no-check-publish",
                    "language": "system",
                    "files": "composer.json",
                    "pass_filenames": False,
                },
                {
                    "id": "php-lint",
                    "name": "php -l",
                    "entry": "php -l",
                    "language": "system",
                    "types": ["php"],
                },
            ],
        }
    ],
    "django": [
        {
            "repo": "https://github.com/adamchainz/django-upgrade",
            "rev": "1.22.2",
            "hooks": [
                {"id": "django-upgrade", "args": ["--target-version", "5.0"]}
            ],
        },
        {
            "repo": "local",
            "hooks": [
                {
                    "id": "django-check",
                    "name": "Django system check",
                    "entry": "python manage.py check",
                    "language": "system",
                    "pass_filenames": False,
                }
            ],
        },
    ],
    "laravel": [
        {
            "repo": "local",
            "hooks": [
                {
                    "id": "composer-validate",
                    "name": "composer validate",
                    "entry": "composer validate --strict --no-check-publish",
                    "language": "system",
                    "files": "composer.json",
                    "pass_filenames": False,
                },
                {
                    "id": "laravel-pint",
                    "name": "Laravel Pint if installed",
                    "entry": "bash -lc './vendor/bin/pint --test 2>/dev/null || vendor/bin/pint --test 2>/dev/null || true'",
                    "language": "system",
                    "types": ["php"],
                    "pass_filenames": False,
                },
                {
                    "id": "laravel-test",
                    "name": "Laravel tests if available",
                    "entry": "bash -lc 'test -f artisan && php artisan test || true'",
                    "language": "system",
                    "pass_filenames": False,
                },
            ],
        }
    ],
    "docker": [
        {
            "repo": "local",
            "hooks": [
                {
                    "id": "hadolint-docker",
                    "name": "Hadolint Dockerfile lint",
                    "entry": "bash -c 'if command -v hadolint >/dev/null 2>&1; then hadolint \"$@\"; else echo \"hadolint not installed; skipping\"; fi' --",
                    "language": "system",
                    "files": "(^|/)Dockerfile(\\..*)?$",
                    "pass_filenames": True,
                }
            ],
        }
    ],
    "markdown": [
        {
            "repo": "https://github.com/DavidAnson/markdownlint-cli2",
            "rev": "v0.44.0",
            "hooks": [{"id": "markdownlint-cli2"}],
        }
    ],
    "yaml": [
        {
            "repo": "https://github.com/pre-commit/pre-commit-hooks",
            "rev": "v5.0.0",
            "hooks": [{"id": "check-yaml"}],
        }
    ],
    "json": [
        {
            "repo": "https://github.com/pre-commit/pre-commit-hooks",
            "rev": "v5.0.0",
            "hooks": [{"id": "check-json"}],
        }
    ],
}


def normalize_env(env: str) -> str:
    key = env.strip().lower()
    if key not in ENV_ALIASES:
        raise ValueError(f"Unknown environment: {env}. Available: {', '.join(AVAILABLE_ENVIRONMENTS)}")
    return ENV_ALIASES[key]


def resolve_environments(envs: list[str]) -> list[str]:
    resolved = []
    def add(env: str):
        normalized = normalize_env(env)
        if normalized in resolved:
            return
        if normalized == "gitleaks":
            add("security")
        elif normalized == "laravel":
            add("php")
        elif normalized == "django":
            add("python")
        resolved.append(normalized)
        
    for env in envs:
        add(env)
    return resolved


def load_config(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {"repos": []}
    data = yaml.safe_load(read_text(path)) or {}
    if not isinstance(data, dict):
        return {"repos": []}
    data.setdefault("repos", [])
    return data


def repo_key(repo: dict[str, Any]) -> str:
    return str(repo.get("repo", ""))


def merge_repos(existing: list[dict[str, Any]], additions: list[dict[str, Any]]) -> list[dict[str, Any]]:
    result = deepcopy(existing)
    for add_repo in additions:
        key = repo_key(add_repo)
        match = next((repo for repo in result if repo_key(repo) == key), None)
        if match is None:
            result.append(deepcopy(add_repo))
            continue
        if "rev" in add_repo:
            match["rev"] = add_repo["rev"]
        match.setdefault("hooks", [])
        existing_ids = {hook.get("id") for hook in match["hooks"] if isinstance(hook, dict)}
        for hook in add_repo.get("hooks", []):
            if hook.get("id") not in existing_ids:
                match["hooks"].append(deepcopy(hook))
    return result


def add_environments(root: Path, environments: list[str], dry_run: bool = False) -> None:
    resolved = resolve_environments(environments)
    config_path = root / CONFIG_FILE
    config = load_config(config_path)
    repos = config.get("repos", [])
    for env in resolved:
        repos = merge_repos(repos, HOOK_GROUPS[env])
        if env == "gitleaks":
            write_gitleaks_config(root, dry_run=dry_run)
            create_detect_secrets_baseline(root, dry_run=dry_run)
            ensure_gitignore(root, dry_run=dry_run)
    config["repos"] = repos
    if config_path.exists():
        backup = backup_file(config_path, dry_run=dry_run)
        if backup:
            echo(f"Backup created: {backup.name}")
    content = yaml.safe_dump(config, sort_keys=False, allow_unicode=True)
    write_text(config_path, content, dry_run=dry_run)


def write_gitleaks_config(root: Path, dry_run: bool = False) -> None:
    path = root / GITLEAKS_CONFIG_FILE
    if path.exists():
        backup_file(path, dry_run=dry_run)
    content = r"""title = "Project Gitleaks Configuration"

[allowlist]
description = "Allow safe examples, fixtures and templates"
paths = [
  "\\.env\\.example$",
  "\\.env\\.template$",
  "docs/examples/.*",
  "tests/fixtures/.*"
]
"""
    write_text(path, content, dry_run=dry_run)


def ensure_gitignore(root: Path, dry_run: bool = False) -> None:
    append_unique_lines(
        root / ".gitignore",
        [
            ".venv/",
            "node_modules/",
            "vendor/",
            ".env",
            ".env.*",
            "!.env.example",
            "!.env.template",
            "dist/",
            "build/",
            "*.spec",
            "*.pyz",
            "*.pem",
            "*.key",
            "*.p12",
            "*.pfx",
            "*.crt",
            "*.cer",
            "*.jks",
            "*.keystore",
            "id_rsa",
            "id_dsa",
            "id_ecdsa",
            "id_ed25519",
            "*.kubeconfig",
            "kubeconfig",
            ".aws/",
            ".gcp/",
            ".azure/",
        ],
        dry_run=dry_run,
    )


def write_safe_add(root: Path, dry_run: bool = False) -> None:
    content = """#!/usr/bin/env bash
set -euo pipefail

if [[ -x "./pre-commit-cli" ]]; then
  ./pre-commit-cli run
elif command -v pre-commit-cli >/dev/null 2>&1; then
  pre-commit-cli run
elif [[ -x ".venv/bin/pre-commit" ]]; then
  .venv/bin/pre-commit run --all-files
elif [[ -x ".venv/python/bin/pre-commit" ]]; then
  .venv/python/bin/pre-commit run --all-files
else
  pre-commit run --all-files
fi

git add "$@"
"""
    path = root / "git-safe-add"
    write_text(path, content, dry_run=dry_run)
    if not dry_run:
        path.chmod(0o755)


def create_detect_secrets_baseline(root: Path, dry_run: bool = False) -> None:
    if (root / ".secrets.baseline").exists():
        return
    # Use a minimal valid baseline; users can regenerate with detect-secrets scan.
    baseline = """{
  "version": "1.5.0",
  "plugins_used": [],
  "filters_used": [],
  "results": {},
  "generated_at": "created-by-pre-commit-cli"
}
"""
    write_text(root / ".secrets.baseline", baseline, dry_run=dry_run)


def fix_config(root: Path, dry_run: bool = False) -> None:
    write_gitleaks_config(root, dry_run=dry_run)
    add_environments(root, ["base", "gitleaks", "shell"], dry_run=dry_run)
