"""Tests for ontolog infer CLI."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest
from typer.testing import CliRunner

from ontolog.cli.main import app
from ontolog.errors import ParseError
from ontolog.models.domain import ProbabilisticDomainModel

FIXTURES = Path(__file__).resolve().parents[1] / "fixtures"
runner = CliRunner()


def test_cli_infer_calls_library_infer(tmp_path: Path) -> None:
    store_path = tmp_path / "ontolog.db"
    model = ProbabilisticDomainModel()

    with patch("ontolog.cli.infer.commands.infer", return_value=model) as mock_infer:
        result = runner.invoke(
            app,
            [
                "infer",
                str(FIXTURES / "controlboard.log"),
                "--store",
                str(store_path),
            ],
        )

    assert result.exit_code == 0, result.output
    mock_infer.assert_called_once()
    assert mock_infer.call_args.args[0] == FIXTURES / "controlboard.log"
    assert mock_infer.call_args.args[1] == store_path


def test_cli_infer_with_nonexistent_path_fails(tmp_path: Path) -> None:
    with patch(
        "ontolog.cli.infer.commands.infer",
        side_effect=ParseError("failed to read source"),
    ):
        result = runner.invoke(
            app,
            [
                "infer",
                str(tmp_path / "missing.log"),
                "--store",
                str(tmp_path / "ontolog.db"),
            ],
        )

    assert result.exit_code != 0
    assert "failed to read source" in result.output


def test_cli_infer_with_custom_store_path(tmp_path: Path) -> None:
    store_path = tmp_path / "custom.db"
    model = ProbabilisticDomainModel()

    with patch("ontolog.cli.infer.commands.infer", return_value=model) as mock_infer:
        result = runner.invoke(
            app,
            [
                "infer",
                str(FIXTURES / "controlboard.log"),
                "--store",
                str(store_path),
            ],
        )

    assert result.exit_code == 0
    assert mock_infer.call_args.args[1] == store_path


def test_cli_infer_with_custom_format(tmp_path: Path) -> None:
    store_path = tmp_path / "ontolog.db"
    model = ProbabilisticDomainModel()

    with patch("ontolog.cli.infer.commands.infer", return_value=model) as mock_infer:
        result = runner.invoke(
            app,
            [
                "infer",
                str(FIXTURES / "controlboard.log"),
                "--store",
                str(store_path),
                "--format",
                "plain",
            ],
        )

    assert result.exit_code == 0
    assert mock_infer.call_args.kwargs["format"].name == "PLAIN"


@pytest.mark.parametrize(
    ("args", "expected_fresh"),
    [
        (["--fresh"], True),
        (["--no-fresh"], False),
    ],
)
def test_cli_infer_fresh_flag(
    tmp_path: Path,
    args: list[str],
    expected_fresh: bool,
) -> None:
    store_path = tmp_path / "ontolog.db"
    model = ProbabilisticDomainModel()

    with patch("ontolog.cli.infer.commands.infer", return_value=model) as mock_infer:
        result = runner.invoke(
            app,
            [
                "infer",
                str(FIXTURES / "controlboard.log"),
                "--store",
                str(store_path),
                *args,
            ],
        )

    assert result.exit_code == 0
    assert mock_infer.call_args.kwargs["fresh"] is expected_fresh
