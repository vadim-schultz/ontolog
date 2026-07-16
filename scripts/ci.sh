#!/usr/bin/env bash
# Run GitHub Actions CI steps locally (mirrors .github/workflows/ci.yml).
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

MATRIX=true
JOB="all"
CI_VENVS="$ROOT/.ci-venvs"

usage() {
    cat <<'EOF'
Usage: scripts/ci.sh [--single] [lint|build|docs|all]

Run CI pipeline steps locally (mirrors .github/workflows/ci.yml).

Commands:
  lint   lint-test job: ruff, mypy, pytest with coverage
  build  build-test job: build wheel/sdist, twine check, smoke install
  docs   docs job: sphinx-build -W
  all    run lint, build, and docs (default)

Options:
  --single  run lint-test once with .venv or Python 3.12
            (default mirrors GitHub Actions: Python 3.11 and 3.12 via uv)

Requires uv (https://docs.astral.sh/uv/) for the default Python matrix.
EOF
}

step() {
    echo ""
    echo "=== $1 ==="
}

require_uv() {
    if ! command -v uv >/dev/null 2>&1; then
        echo "error: uv is required; install from https://docs.astral.sh/uv/" >&2
        exit 1
    fi
}

ensure_python() {
    local version="$1"
    require_uv
    uv python install "$version"
}

resolve_python() {
    local version="$1"

    ensure_python "$version"

    if command -v "python${version}" >/dev/null 2>&1; then
        command -v "python${version}"
        return
    fi

    # Avoid picking up this project's .venv when resolving managed interpreters.
    (cd /tmp && uv python find "$version" --managed-python --no-project)
}

setup_ci_venv() {
    local version="$1"
    local interpreter="$2"
    local venv="$CI_VENVS/$version"

    if [[ ! -x "$venv/bin/python" ]]; then
        uv venv "$venv" --python "$interpreter" --quiet
    fi

    uv pip install --python "$venv" -e ".[dev]"
    echo "$venv/bin/python"
}

python_for_version() {
    local version="$1"
    local interpreter python

    interpreter="$(resolve_python "$version")"
    python="$(setup_ci_venv "$version" "$interpreter")"
    echo "$python"
}

resolve_single_python() {
    if [[ -x "$ROOT/.venv/bin/python" ]]; then
        echo "$ROOT/.venv/bin/python"
        return
    fi

    python_for_version 3.12
}

install_dev_deps() {
    local python="$1"

    if command -v uv >/dev/null 2>&1; then
        uv pip install --python "$python" -e ".[dev]"
    else
        "$python" -m pip install --upgrade pip
        "$python" -m pip install -e ".[dev]"
    fi
}

run_lint_test() {
    local python="$1"

    step "Install dev dependencies ($python)"
    install_dev_deps "$python"

    step "Ruff check"
    "$python" -m ruff check src tests examples benchmarks

    step "Ruff format"
    "$python" -m ruff format --check src tests examples benchmarks

    step "Mypy"
    "$python" -m mypy src

    step "Pytest with coverage"
    "$python" -m pytest --cov=ontolog --cov-report=xml --cov-report=term
}

run_lint_test_matrix() {
    local version python

    for version in 3.11 3.12; do
        echo ""
        echo ">>> lint-test with Python $version"
        python="$(python_for_version "$version")"
        run_lint_test "$python"
    done
}

run_lint_test_single() {
    local python
    python="$(resolve_single_python)"
    echo ">>> lint-test with $python"
    run_lint_test "$python"
}

run_build_test() {
    local python
    python="$(resolve_single_python)"

    step "Install build tools"
    if command -v uv >/dev/null 2>&1; then
        uv pip install --python "$python" build twine
    else
        "$python" -m pip install --upgrade pip
        "$python" -m pip install build twine
    fi

    step "Clean previous build artifacts"
    rm -rf dist build src/*.egg-info

    step "Build package"
    "$python" -m build

    step "Check package"
    twine check dist/*

    step "Test install from wheel"
    if command -v uv >/dev/null 2>&1; then
        uv pip install --python "$python" dist/*.whl
    else
        "$python" -m pip install dist/*.whl
    fi
    ontolog --version
    "$python" -c "import ontolog; print(ontolog.__version__)"
}

run_docs() {
    local python
    python="$(resolve_single_python)"

    step "Install docs dependencies"
    if command -v uv >/dev/null 2>&1; then
        uv pip install --python "$python" -e ".[docs]"
    else
        "$python" -m pip install --upgrade pip
        "$python" -m pip install -e ".[docs]"
    fi

    step "Sphinx build"
    "$python" -m sphinx -W -b html docs docs/_build
}

while [[ $# -gt 0 ]]; do
    case "$1" in
        --single)
            MATRIX=false
            shift
            ;;
        --matrix)
            MATRIX=true
            shift
            ;;
        -h | --help)
            usage
            exit 0
            ;;
        lint | build | docs | all)
            JOB="$1"
            shift
            ;;
        *)
            echo "error: unknown argument: $1" >&2
            usage >&2
            exit 1
            ;;
    esac
done

case "$JOB" in
    lint)
        if [[ "$MATRIX" == true ]]; then
            run_lint_test_matrix
        else
            run_lint_test_single
        fi
        ;;
    build)
        run_build_test
        ;;
    docs)
        run_docs
        ;;
    all)
        if [[ "$MATRIX" == true ]]; then
            run_lint_test_matrix
        else
            run_lint_test_single
        fi
        run_build_test
        run_docs
        ;;
esac
