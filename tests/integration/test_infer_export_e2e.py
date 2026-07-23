"""End-to-end integration tests for infer and export."""

from __future__ import annotations

from pathlib import Path

from typer.testing import CliRunner

from ontolog.cli.main import app

FIXTURES = Path(__file__).resolve().parents[1] / "fixtures"
runner = CliRunner()


def test_infer_exports_mermaid() -> None:
    result = runner.invoke(
        app,
        [
            "infer",
            str(FIXTURES / "controlboard.log"),
            "--format",
            "mermaid",
        ],
    )
    assert result.exit_code == 0, result.output
    assert "erDiagram" in result.stdout
    assert "Interface" in result.stdout or "Controlboard" in result.stdout
