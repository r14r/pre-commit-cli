# pre-commit-cli Python Project

`pre-commit-cli` is a Python CLI for creating, detecting, repairing and running `pre-commit` hook configurations without relying on Homebrew. It is designed for older macOS setups and project-local Python virtual environments.

## Main features

- Python package with helper modules under `src/pre_commit_cli/libmodules`
- Supports the old flag-based interface:
  - `--setup`
  - `--add ENV`
  - `--detect`
  - `--run [HOOK]`
  - `--doctor`
  - `--status`
  - `--install-hook`
  - `--autoupdate`
  - `--ci github`
  - `--list`
  - `--init-git`
  - `--no-install`
  - `--dry-run`
  - `--version`
- Supports subcommands:
  - `setup`
  - `add ENV`
  - `detect`
  - `run [HOOK]`
  - `doctor`
  - `status`
  - `install-hook`
  - `autoupdate`
  - `ci github`
  - `list`
  - `init-git`
  - `fix-config`
  - `fix-gitleaks-config`
  - `fix-shfmt-config`
  - `safe-add -- .`
- Creates or updates `.pre-commit-config.yaml`
- Writes a valid `.gitleaks.toml`
- Creates `.secrets.baseline`
- Updates `.gitignore`
- Generates GitHub Actions CI workflow
- Includes PyInstaller and shiv build commands

## Install for development

```bash
just setup
```

Or manually:

```bash
python3 -m venv .venv
.venv/bin/python -m pip install --upgrade pip setuptools wheel
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python -m pip install -e .
```

## Usage from source

```bash
./pre-commit-cli --help
./pre-commit-cli --setup
./pre-commit-cli --detect
./pre-commit-cli --status
./pre-commit-cli --run
```

## Usage after editable install

```bash
pre-commit-cli --setup
pre-commit-cli --add python
pre-commit-cli --add laravel
pre-commit-cli --run
```

## Build standalone with PyInstaller

```bash
just build-pyinstaller
```

Result:

```text
dist/pre-commit-cli
```

## Build standalone `.pyz` with shiv

```bash
just build-shiv
```

Result:

```text
dist/pre-commit-cli.pyz
```

Run it:

```bash
python dist/pre-commit-cli.pyz --help
```

## Hook groups

| Environment | Hooks |
|---|---|
| `base` | YAML, JSON, TOML, EOF, trailing whitespace, line endings |
| `gitleaks` / `security` | Gitleaks and detect-secrets |
| `shell` | shfmt and shellcheck |
| `python` | Ruff and Ruff Format |
| `node` | optional npm lint/test local hooks |
| `php` | Composer validate and PHP lint |
| `django` | Django system check |
| `laravel` | Laravel Pint and Laravel tests when available |

## Recommended workflow

```bash
pre-commit-cli --init-git
pre-commit-cli --setup
pre-commit-cli --detect
pre-commit-cli --doctor
pre-commit-cli --run
```

## Notes

The tool deliberately avoids `brew install pre-commit`. It creates or uses a project-local `.venv` and installs `pre-commit` there. This avoids Homebrew/Python incompatibilities on older macOS versions.

## Repository quality checks

This repository uses `.pre-commit-config.yaml` with locally installed tools.
No Homebrew installation is required.

```bash
git pull origin main
just precommit-bootstrap # creates .venv/python, installs .[dev], installs commit/push hooks
just precommit-validate
just precommit        # all regular hooks on all files
just precommit-all    # regular + pytest, Bandit and pip-audit manual hooks
just precommit-fix    # fix Ruff lint and formatting problems in src/
```

Additional commands: `just precommit-staged`, `just precommit-test`,
`just precommit-security`, `just precommit-install`,
`just precommit-uninstall`, and `just precommit-clean`.

Regular hooks use read-only Ruff checks to prevent silent changes during a
commit. Whitespace and EOF hooks can update files; stage the resulting changes
and rerun the command. The full Python dependency vulnerability scan is run by
`just precommit-security` and the CI quality workflow.

The update-cli `setup` workflow bootstraps the QA dependencies, runs
pre-commit, builds the application and deploys it. The CI `quality.yml`
workflow runs the same checks on pushes and pull requests.
