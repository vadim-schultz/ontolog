"""Tests for ontolog CLI."""

from __future__ import annotations

from typer.testing import CliRunner

import ontolog
from ontolog.cli.main import app

runner = CliRunner()


def test_version_flag() -> None:
    result = runner.invoke(app, ["--version"], color=False)
    assert result.exit_code == 0
    assert result.stdout == f"{ontolog.__version__}\n"


def test_help() -> None:
    result = runner.invoke(app, ["--help"], color=False)
    assert result.exit_code == 0
    assert "ontolog" in result.stdout.lower()
    assert "--version" in result.stdout


def test_no_args_shows_help() -> None:
    result = runner.invoke(app, [], color=False)
    assert result.exit_code == 2
    assert "Usage:" in result.stdout
