# Ontolog

**Probabilistic domain-model inference from application logs**

[![CI](https://github.com/vadim-schultz/ontolog/actions/workflows/ci.yml/badge.svg)](https://github.com/vadim-schultz/ontolog/actions/workflows/ci.yml)
[![Documentation Status](https://readthedocs.org/projects/ontolog/badge/?version=latest)](https://ontolog.readthedocs.io/en/latest/?badge=latest)
[![codecov](https://codecov.io/gh/vadim-schultz/ontolog/branch/main/graph/badge.svg)](https://codecov.io/gh/vadim-schultz/ontolog)
[![PyPI version](https://img.shields.io/pypi/v/ontolog)](https://pypi.org/project/ontolog/)
[![Python versions](https://img.shields.io/pypi/pyversions/ontolog)](https://pypi.org/project/ontolog/)
[![License](https://img.shields.io/pypi/l/ontolog)](https://github.com/vadim-schultz/ontolog/blob/main/LICENSE)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)
[![Checked with mypy](https://www.mypy-lang.org/static/mypy_badge.svg)](https://mypy-lang.org/)
[![Typing: Strict](https://img.shields.io/badge/typing-strict-blue)](https://github.com/vadim-schultz/ontolog/blob/main/pyproject.toml)

Ontolog ingests raw logs, extracts templates with Drain3, accumulates deterministic evidence about
entities, fields, relationships, and state transitions, and optionally augments that evidence with
semantic annotations from user-provided LLM providers. The output is a probabilistic domain model
exportable as Pydantic models, JSON Schema, Mermaid diagrams, or property graphs.

**Status:** Chapter 0 scaffold — library skeleton and CI/CD baseline. Inference pipeline lands in
later chapters; see [IMPLEMENTATION_PLAN.md](IMPLEMENTATION_PLAN.md).

## Install

```bash
pip install ontolog
```

## Development

```bash
git clone https://github.com/vadim-schultz/ontolog.git
cd ontolog
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
pytest
```

## Documentation

- [Read the Docs](https://ontolog.readthedocs.io)
- [Implementation plan](IMPLEMENTATION_PLAN.md)
- [Contributing](CONTRIBUTING.md)

## License

MIT — see [LICENSE](LICENSE).
