# pre-commit-cli

Native Go command-line utility for detecting project languages, generating and extending pre-commit hooks, and running diagnostics.

## Requirements

- Go 1.22 or later to build the CLI.
- Git.
- Python and the upstream `pre-commit` package only when running or installing hooks. The CLI itself is a compiled Go executable.

## Bootstrap, test, build and install

```bash
go mod tidy
just fmt
just precommit
just build
just install
```

To change the installation directory:

```bash
DEPLOY_PATH="$HOME/.local/bin" just install
```

Or run `u setup --noui` using `update-cli.yaml`.

## CLI usage

```bash
pre-commit-cli --help
pre-commit-cli version
pre-commit-cli setup
pre-commit-cli detect
pre-commit-cli add go
pre-commit-cli add python
pre-commit-cli status
pre-commit-cli doctor
pre-commit-cli run
pre-commit-cli run go-vet
pre-commit-cli autoupdate
pre-commit-cli install-hook
pre-commit-cli safe-add -- .
```

Legacy flag syntax such as `--setup`, `--detect`, `--run`, `--doctor`, `--status`, and `--version` is supported.

## Project-local development checks

```bash
just fmt
just check
just test
just precommit
just precommit-bootstrap
```

The source of truth is `main.go` and `go.mod`. Python source files from the previous implementation are legacy material and are not used to compile or install the Go CLI.

## Migration limitations

The Go implementation covers the primary commands, environment detection and configuration merging. Not every specialized generated file and hook behavior of the Python version is fully ported yet. Validate configuration changes before using the CLI in production.
