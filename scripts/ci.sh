#!/usr/bin/env bash
# Run GitHub Actions CI steps locally (mirrors .github/workflows/ci.yml).
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

MATRIX=false
JOB="all"

usage() {
    cat <<'EOF'
Usage: scripts/ci.sh [--matrix] [lint|build|docs|all]

Run CI pipeline steps locally (mirrors .github/workflows/ci.yml).

Commands:
  lint   lint-test job: ruff, mypy, pytest with coverage
  build  build-test job: build wheel/sdist, twine check, smoke install
  docs   docs job: sphinx-build -W
  all    run lint, build, and docs (default)

Options:
  --matrix  run lint-test under python3.11 and python3.12 when available
EOF
}

step() {
    echo ""
    echo "=== $1 ==="
}

run_lint_test() {
    local python="${1:-python}"

    step "Install dev dependencies ($python)"
    "$python" -m pip install --upgrade pip
    "$python" -m pip install -e ".[dev]"

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
    local found=0
    for py in python3.11 python3.12; do
        if command -v "$py" >/dev/null 2>&1; then
            found=1
            echo ""
            echo ">>> lint-test with $py"
            run_lint_test "$py"
        else
            echo "warning: $py not found on PATH, skipping" >&2
        fi
    done
    if [[ "$found" -eq 0 ]]; then
        echo "warning: no matrix interpreters found, using current python" >&2
        run_lint_test python
    fi
}

run_build_test() {
    step "Install build tools"
    python -m pip install --upgrade pip
    python -m pip install build twine

    step "Clean previous build artifacts"
    rm -rf dist build src/*.egg-info

    step "Build package"
    python -m build

    step "Check package"
    twine check dist/*

    step "Test install from wheel"
    python -m pip install dist/*.whl
    ontolog --version
    python -c "import ontolog; print(ontolog.__version__)"
}

run_docs() {
    step "Install docs dependencies"
    python -m pip install --upgrade pip
    python -m pip install -e ".[docs]"

    step "Sphinx build"
    sphinx-build -W -b html docs docs/_build
}

while [[ $# -gt 0 ]]; do
    case "$1" in
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
            run_lint_test python
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
            run_lint_test python
        fi
        run_build_test
        run_docs
        ;;
esac
