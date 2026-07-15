# Releasing

Version is defined in `pyproject.toml` (`[project].version`) and mirrored in
`src/ontolog/__init__.py` (`__version__`) and `docs/conf.py` (`release`).

## Process

1. Bump version in all three locations.
2. Update `CHANGELOG.md`.
3. Merge to `main`.
4. The **Release on Main Merge** workflow tags `v<version>`, creates a GitHub release, and
   optionally publishes to PyPI when the repository variable `ENABLE_PYPI_PUBLISH` is `true`.

## PyPI trusted publishing

Configure [PyPI trusted publishing](https://docs.pypi.org/trusted-publishers/) before enabling
`ENABLE_PYPI_PUBLISH`. Until then, use **Manual PyPI Publish** (`publish.yml`) after creating a
GitHub release.

See [CONTRIBUTING.md](https://github.com/vadim-schultz/ontolog/blob/main/CONTRIBUTING.md) for
maintainer setup details.
