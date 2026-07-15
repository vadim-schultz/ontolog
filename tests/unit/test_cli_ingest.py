"""Tests for ontolog ingest CLI."""

from __future__ import annotations

from pathlib import Path

from typer.testing import CliRunner

from ontolog import LogRecord
from ontolog.cli.main import app

FIXTURES = Path(__file__).resolve().parents[1] / "fixtures"
runner = CliRunner()


def test_ingest_controlboard_jsonl_stdout() -> None:
    result = runner.invoke(app, ["ingest", str(FIXTURES / "controlboard.log")])

    assert result.exit_code == 0, result.output
    lines = [line for line in result.stdout.splitlines() if line.strip()]
    assert len(lines) >= 50
    LogRecord.model_validate_json(lines[0])


def test_ingest_json_format() -> None:
    result = runner.invoke(
        app,
        ["ingest", str(FIXTURES / "sample.jsonl"), "--format", "json"],
    )

    assert result.exit_code == 0
    assert len(result.stdout.splitlines()) == 6


def test_ingest_limit() -> None:
    result = runner.invoke(
        app,
        ["ingest", str(FIXTURES / "controlboard.log"), "--limit", "1"],
    )

    assert result.exit_code == 0
    assert len(result.stdout.splitlines()) == 1


def test_ingest_parse_error_exits_nonzero(tmp_path: Path) -> None:
    bad = tmp_path / "bad.log"
    bad.write_text("not syslog\n", encoding="utf-8")

    result = runner.invoke(app, ["ingest", str(bad), "--format", "syslog"])

    assert result.exit_code != 0
