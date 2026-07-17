"""Tests for ontolog export CLI."""

from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

from ontolog.cli.main import app

FIXTURES = Path(__file__).resolve().parents[1] / "fixtures"
runner = CliRunner()


def _prepare_store(tmp_path: Path) -> Path:
    store_path = tmp_path / "ontolog.db"
    result = runner.invoke(
        app,
        [
            "templates",
            str(FIXTURES / "controlboard.log"),
            "--store",
            str(store_path),
        ],
    )
    assert result.exit_code == 0
    return store_path


def test_export_pydantic_stdout(tmp_path: Path) -> None:
    store_path = _prepare_store(tmp_path)
    result = runner.invoke(
        app,
        ["export", "pydantic", "--store", str(store_path)],
    )
    assert result.exit_code == 0, result.output
    assert "class Interface" in result.stdout


def test_export_json_schema_stdout(tmp_path: Path) -> None:
    store_path = _prepare_store(tmp_path)
    result = runner.invoke(
        app,
        ["export", "json-schema", "--store", str(store_path)],
    )
    assert result.exit_code == 0, result.output
    schema = json.loads(result.stdout)
    assert "properties" in schema


def test_export_mermaid_stdout(tmp_path: Path) -> None:
    store_path = _prepare_store(tmp_path)
    result = runner.invoke(
        app,
        ["export", "mermaid", "--store", str(store_path)],
    )
    assert result.exit_code == 0, result.output
    assert "erDiagram" in result.stdout


def test_export_unknown_format(tmp_path: Path) -> None:
    store_path = _prepare_store(tmp_path)
    result = runner.invoke(
        app,
        ["export", "not-a-format", "--store", str(store_path)],
    )
    assert result.exit_code != 0


def test_export_all_includes_ineligible(tmp_path: Path) -> None:
    store_path = _prepare_store(tmp_path)
    default_result = runner.invoke(
        app,
        ["export", "markdown", "--store", str(store_path)],
    )
    all_result = runner.invoke(
        app,
        ["export", "markdown", "--store", str(store_path), "--all"],
    )
    assert default_result.exit_code == 0
    assert all_result.exit_code == 0
    assert len(all_result.stdout) >= len(default_result.stdout)
