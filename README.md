# pre-commit-cli

A native Go CLI for detecting project languages, managing pre-commit hook configurations, installing hooks, and running project diagnostics.

## Build requirements

- Go 1.22+
- Git
- Optional: Python and upstream `pre-commit` **only for executing/installing the hook framework in target projects**, not for building this CLI

## Develop and install

```bash
just bootstrap
just fmt
just precommit
just build
just install
```

To install outside `/usr/local/bin`:

```bash
DEPLOY_PATH="$HOME/.local/bin" just install
```

Or use `u setup --noui`, driven by the Go-only `update-cli.yaml`.

## Commands

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

## Quality checks

```bash
just fmt               # gofmt all Go files
just check             # check formatting and go vet
just test              # go test
just precommit         # formatting, vet, tests
just precommit-fix     # fix formatting
```

The application itself contains no Python source or Python packaging/build tooling. Python support in detected target projects remains intentional.

The Go implementation is a migration of the main CLI features; specialized generated security files and hooks from the previous implementation may not have full feature parity.
