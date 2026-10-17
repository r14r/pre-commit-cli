set shell := ["bash", "-eu", "-o", "pipefail", "-c"]

APP := "pre-commit-cli"
DEPLOY_DIR := env_var_or_default("DEPLOY_PATH", "/usr/local/bin")

# Help
default:
    @just --list

# Dependencies
bootstrap:
    @go mod download
    @go mod verify

# Go formatting
fmt:
    @gofmt -w .

# Static checks
check:
    @files="$(gofmt -l .)"; if [ -n "$files" ]; then echo "Go files need formatting:"; echo "$files"; exit 1; fi
    @go vet ./...

# Tests
test:
    @go test ./...

# Build
build:
    @mkdir -p dist
    @go build -trimpath -ldflags "-s -w" -o dist/{{APP}} .

# Install binary
install: build
    @mkdir -p "{{DEPLOY_DIR}}"
    @install -m 0755 dist/{{APP}} "{{DEPLOY_DIR}}/{{APP}}"

# Run Go CLI
run *args:
    @go run . {{args}}

# Git hooks and quality checks
precommit-bootstrap:
    @if command -v pre-commit >/dev/null 2>&1; then pre-commit install --hook-type pre-commit --hook-type pre-push; else echo "Upstream pre-commit is optional; install it to activate Git hooks."; fi

precommit:
    @just check
    @just test

precommit-all:
    @just precommit

precommit-fix:
    @just fmt

# Clean artifacts
clean:
    @rm -rf dist

# Version
version:
    @go run . version
