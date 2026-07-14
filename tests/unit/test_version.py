"""Smoke tests for package metadata."""

from __future__ import annotations

import tomllib
from pathlib import Path

import ontolog


def test_version_is_string() -> None:
    assert isinstance(ontolog.__version__, str)
    assert ontolog.__version__


def test_version_matches_pyproject() -> None:
    pyproject = tomllib.loads(Path("pyproject.toml").read_text(encoding="utf-8"))
    assert ontolog.__version__ == pyproject["project"]["version"]
