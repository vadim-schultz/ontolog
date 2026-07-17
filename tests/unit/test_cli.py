"""Tests for ontolog CLI."""

from __future__ import annotations

import re

from typer.testing import CliRunner, Result

import ontolog
from ontolog.cli.main import app

runner = CliRunner()
_ANSI_ESCAPE = re.compile(r"\x1b\[[0-9;]*[a-zA-Z]")
_CLI_ENV = {"NO_COLOR": "1", "TERM": "dumb"}


def _plain_output(text: str) -> str:
    """Strip ANSI escapes so assertions work when Rich splits styled option names."""
    return _ANSI_ESCAPE.sub("", text)


def _invoke(*args: object, **kwargs: object) -> Result:
    env = {**_CLI_ENV, **kwargs.pop("env", {})}
    return runner.invoke(*args, color=False, env=env, **kwargs)


def test_version_flag() -> None:
    result = _invoke(app, ["--version"])
    assert result.exit_code == 0
    assert _plain_output(result.stdout) == f"{ontolog.__version__}\n"


def test_help() -> None:
    result = _invoke(app, ["--help"])
    output = _plain_output(result.stdout)
    assert result.exit_code == 0
    assert "ontolog" in output.lower()
    assert "--version" in output


def test_no_args_shows_help() -> None:
    result = _invoke(app, [])
    output = _plain_output(result.stdout)
    assert result.exit_code == 2
    assert "Usage:" in output
