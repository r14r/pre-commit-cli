set shell := ["bash", "-eu", "-o", "pipefail", "-c"]

APP := "pre-commit-cli"
export VIRTUAL_ENV := ".venv/python"
VENV := ".venv"
BIN := VENV + "/python/bin"
CLI := BIN + "/" + APP
DEPLOY_DIR := "/Users/Shared/CLOUD/DeveloperTools/bin"
DEPLOY_TARGET := DEPLOY_DIR + "/" + APP

# Show available commands
help:
    @just --list

# Create virtualenv using venv setup python
setup-env:
    venv setup python
    direnv-allow

# Install editable package into current venv
install-env:
    uv pip install -e .

# Run CLI help
cli-help:
    {{BIN}}/{{APP}} --help

# Run the CLI from source without installing
run *args:
    {{BIN}}/python -m pre_commit_cli {{args}}

# Run a quick syntax check
check:
    {{BIN}}/python -m compileall src

# Show package version information
version:
    {{BIN}}/{{APP}} --version

# Build standalone binary using PyInstaller
build-pyinstaller:
    rm -rf build dist/pyinstaller dist/*.spec
    mkdir -p dist/pyinstaller
    {{BIN}}/pyinstaller --onefile --name {{APP}} --distpath dist/pyinstaller src/pre_commit_cli/__main__.py
    echo "pyinstaller" > dist/pyinstaller/build_source.txt

# Build standalone pyz using shiv
build-shiv:
    rm -rf dist/shiv
    mkdir -p dist/shiv
    {{BIN}}/shiv -c {{APP}} -o dist/shiv/{{APP}}.pyz .
    echo "shiv" > dist/shiv/build_source.txt

# Build standalone binary using PyOxidizer
build-pyoxidizer:
    rm -rf dist/pyoxidizer build/x86_64-apple-darwin
    {{BIN}}/pyoxidizer build install
    mkdir -p dist/pyoxidizer
    cp -R build/x86_64-apple-darwin/*/install/ dist/pyoxidizer/
    echo "pyoxidizer" > dist/pyoxidizer/build_source.txt

# Build standalone package (options: "pyinstaller", "shiv", "pyoxidizer", default: "pyoxidizer")
build tool="pyoxidizer":
    @if [ "{{tool}}" = "shiv" ]; then \
        just build-shiv; \
    elif [ "{{tool}}" = "pyinstaller" ]; then \
        just build-pyinstaller; \
    elif [ "{{tool}}" = "pyoxidizer" ]; then \
        just build-pyoxidizer; \
    else \
        echo "Error: Unknown build tool '{{tool}}'. Must be 'pyinstaller', 'shiv' or 'pyoxidizer'."; \
        exit 1; \
    fi

# Build all standalone artifacts
build-all: build-pyinstaller build-shiv build-pyoxidizer

# Run generated shiv package
run-shiv *args:
    {{BIN}}/python dist/shiv/{{APP}}.pyz {{args}}

# Deploy compiled binary to DeveloperTools/bin (options: "pyinstaller", "shiv", "pyoxidizer", default: "pyoxidizer")
deploy tool="pyoxidizer":
    @if [ "{{tool}}" = "pyinstaller" ]; then \
        if [ ! -f "dist/pyinstaller/{{APP}}" ]; then \
            just build pyinstaller; \
        fi; \
        mkdir -p {{DEPLOY_DIR}}; \
        cp -f dist/pyinstaller/{{APP}} {{DEPLOY_TARGET}}; \
        chmod +x {{DEPLOY_TARGET}}; \
        echo "Deployed PyInstaller version to {{DEPLOY_TARGET}}"; \
    elif [ "{{tool}}" = "shiv" ]; then \
        if [ ! -f "dist/shiv/{{APP}}.pyz" ]; then \
            just build shiv; \
        fi; \
        mkdir -p {{DEPLOY_DIR}}; \
        cp -f dist/shiv/{{APP}}.pyz {{DEPLOY_TARGET}}; \
        chmod +x {{DEPLOY_TARGET}}; \
        echo "Deployed Shiv version to {{DEPLOY_TARGET}}"; \
    elif [ "{{tool}}" = "pyoxidizer" ]; then \
        if [ ! -d "dist/pyoxidizer" ]; then \
            just build pyoxidizer; \
        fi; \
        mkdir -p {{DEPLOY_DIR}}; \
        cp -f dist/pyoxidizer/{{APP}} {{DEPLOY_TARGET}}; \
        rm -rf {{DEPLOY_DIR}}/lib; \
        cp -R dist/pyoxidizer/lib {{DEPLOY_DIR}}/lib; \
        chmod +x {{DEPLOY_TARGET}}; \
        echo "Deployed PyOxidizer version to {{DEPLOY_TARGET}}"; \
    else \
        echo "Error: Unknown deploy tool '{{tool}}'. Must be 'pyinstaller', 'shiv' or 'pyoxidizer'."; \
        exit 1; \
    fi
    @{{DEPLOY_TARGET}} --version

# Clean generated files
clean:
    rm -rf build dist *.egg-info src/*.egg-info src/pre_commit_cli.egg-info .pytest_cache

# Create project ZIP
zip:
    cd .. && zip -r {{APP}}-python-project.zip {{APP}}-python-project -x '{{APP}}-python-project/.venv/*' '{{APP}}-python-project/dist/*' '{{APP}}-python-project/build/*'
