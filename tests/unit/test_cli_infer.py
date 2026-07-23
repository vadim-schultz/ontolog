"""Tests for ontolog infer CLI."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

from typer.testing import CliRunner

from ontolog.cli.main import app
from ontolog.export import ExportOptions
from ontolog.models.domain import ProbabilisticDomainModel
from ontolog.pipeline import InferOutput

FIXTURES = Path(__file__).resolve().parents[1] / "fixtures"
runner = CliRunner()


def test_cli_infer_requires_format() -> None:
    result = runner.invoke(app, ["infer", str(FIXTURES / "controlboard.log")])

    assert result.exit_code != 0


def test_cli_infer_rejects_unknown_format() -> None:
    result = runner.invoke(
        app,
        ["infer", str(FIXTURES / "controlboard.log"), "--format", "not-a-format"],
    )

    assert result.exit_code != 0


def test_cli_infer_help_lists_export_formats() -> None:
    result = runner.invoke(app, ["infer", "--help"])

    assert result.exit_code == 0
    assert "pydantic|json-schema|" in result.stdout


def test_cli_infer_prints_mermaid_to_stdout() -> None:
    result = runner.invoke(
        app,
        ["infer", str(FIXTURES / "controlboard.log"), "--format", "mermaid"],
    )

    assert result.exit_code == 0, result.output
    assert "erDiagram" in result.stdout


def test_cli_infer_log_format_option() -> None:
    result = runner.invoke(
        app,
        [
            "infer",
            str(FIXTURES / "controlboard.log"),
            "--format",
            "markdown",
            "--log-format",
            "plain",
        ],
    )

    assert result.exit_code == 0, result.output
    assert result.stdout


def test_cli_infer_all_and_provenance_flags() -> None:
    model = ProbabilisticDomainModel()
    output = InferOutput(model=model, artifact="report")

    with patch("ontolog.cli.infer.commands.infer", return_value=output) as mock_infer:
        result = runner.invoke(
            app,
            [
                "infer",
                str(FIXTURES / "controlboard.log"),
                "--format",
                "markdown",
                "--all",
                "--provenance",
            ],
        )

    assert result.exit_code == 0, result.output
    export_options = mock_infer.call_args.kwargs["export_options"]
    assert isinstance(export_options, ExportOptions)
    assert export_options.include_ineligible is True
    assert export_options.include_provenance is True


def test_cli_infer_with_nonexistent_path_fails(tmp_path: Path) -> None:
    result = runner.invoke(
        app,
        [
            "infer",
            str(tmp_path / "missing.log"),
            "--format",
            "mermaid",
        ],
    )

    assert result.exit_code != 0
