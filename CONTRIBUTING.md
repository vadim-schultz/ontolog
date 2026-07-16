# Contributing

## Setup

With [uv](https://docs.astral.sh/uv/) (recommended):

```bash
uv sync --extra dev
```

Or with pip:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

Optional: install pre-commit hooks.

```bash
pre-commit install
```

## Checks

Run the full CI pipeline locally before pushing:

```bash
./scripts/ci.sh              # all CI jobs (Python 3.11 + 3.12 via uv, like GitHub Actions)
./scripts/ci.sh lint         # lint-test only
./scripts/ci.sh --single     # faster: one interpreter (.venv or Python 3.12)
./scripts/ci.sh build        # build-test only
./scripts/ci.sh docs         # docs only
```

The default matrix uses `uv python install` to download missing interpreters and
runs each version in `.ci-venvs/` without touching your project `.venv`.

Or run individual checks:

```bash
ruff check src tests examples benchmarks
ruff format src tests examples benchmarks
mypy src
pytest
```

## Docs

```bash
pip install -e ".[docs]"
sphinx-build -W -b html docs docs/_build
```

Pull requests should keep CI green (Ruff, Mypy, Pytest, Sphinx `-W`).

## Code coverage (Codecov)

CI uploads `coverage.xml` to [Codecov](https://codecov.io) on Python 3.12.

**Repository maintainers:** add a Codecov upload token for reliable uploads:

1. Sign in at [codecov.io](https://codecov.io) with GitHub and enable the `ontolog` repository.
2. In GitHub: **Settings → Secrets and variables → Actions → New repository secret**
   - Name: `CODECOV_TOKEN`
   - Value: the token from Codecov project settings.

## Publishing to PyPI (trusted publishing)

Releases can be published via [`.github/workflows/publish.yml`](.github/workflows/publish.yml) using
[PyPI trusted publishing](https://docs.pypi.org/trusted-publishers/) (OIDC).

**One-time PyPI setup (account owner):**

1. Create a [PyPI](https://pypi.org) account with 2FA enabled.
2. **Account settings → Publishing → Add a new pending publisher**
   - **PyPI project name:** `ontolog`
   - **Owner:** `vadim-schultz`
   - **Repository name:** `ontolog`
   - **Workflow name:** `publish.yml`
3. Set repository variable `ENABLE_PYPI_PUBLISH` to `true` to enable automatic publish on main
   merge (optional; manual publish works without it).

## Implementation plan

Work is organized in chapters — see [`.plans/IMPLEMENTATION_PLAN.md`](.plans/IMPLEMENTATION_PLAN.md). Each
chapter should land as a focused PR with green CI before the next begins.
