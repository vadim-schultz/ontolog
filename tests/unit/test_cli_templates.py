"""Tests for ontolog templates CLI."""

from __future__ import annotations

from pathlib import Path

from typer.testing import CliRunner

from ontolog.cli.main import app

FIXTURES = Path(__file__).resolve().parents[1] / "fixtures"
runner = CliRunner()


def test_templates_command_exits_zero() -> None:
    result = runner.invoke(
        app,
        ["templates", str(FIXTURES / "controlboard.log"), "--no-store"],
    )

    assert result.exit_code == 0, result.output


def test_templates_output_contains_packet_sent() -> None:
    result = runner.invoke(
        app,
        ["templates", str(FIXTURES / "controlboard.log"), "--no-store"],
    )

    assert result.exit_code == 0
    assert "PacketSent" in result.stdout


def test_templates_status_on_stderr() -> None:
    result = runner.invoke(
        app,
        ["templates", str(FIXTURES / "controlboard.log"), "--no-store"],
    )

    assert result.exit_code == 0
    assert "extracted" in result.stderr


def test_templates_no_store_flag(tmp_path: Path) -> None:
    db_path = tmp_path / "should-not-exist.db"
    result = runner.invoke(
        app,
        [
            "templates",
            str(FIXTURES / "controlboard.log"),
            "--no-store",
            "--store",
            str(db_path),
        ],
    )

    assert result.exit_code == 0
    assert not db_path.exists()
