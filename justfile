set shell := ["bash", "-eu", "-o", "pipefail", "-c"]

APP := "pre-commit-cli"
DEPLOY_DIR := env_var_or_default("DEPLOY_PATH", "/usr/local/bin")

# Help
default:
    @just --list

# Dependencies
bootstrap:
    @go mod download
    @gofmt -w main.go main_test.go

# Go formatting and static checks
fmt:
    @gofmt -w main.go

check:
    @test -z "$(gofmt -l main.go main_test.go)" || { echo "Go files need formatting"; gofmt -l main.go; exit 1; }
    @go vet ./...

# Tests
test:
    @go test ./...

# Build
build:
    @mkdir -p dist
    @go build -trimpath -ldflags "-s -w" -o dist/{{APP}} .

# Install binary; override DEPLOY_PATH to change target
install: build
    @mkdir -p "{{DEPLOY_DIR}}"
    @install -m 0755 dist/{{APP}} "{{DEPLOY_DIR}}/{{APP}}"

# Run the Go CLI
run *args:
    @go run . {{args}}

# Git hooks and quality checks
precommit-bootstrap:
    @if command -v pre-commit >/dev/null 2>&1; then pre-commit install --hook-type pre-commit --hook-type pre-push; else echo "Install pre-commit or run pre-commit-cli setup"; fi

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

# Show version
version:
    @go run . version
