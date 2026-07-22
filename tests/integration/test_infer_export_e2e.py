"""End-to-end integration tests for infer and export."""

from __future__ import annotations

from pathlib import Path

from typer.testing import CliRunner

from ontolog.cli.main import app

FIXTURES = Path(__file__).resolve().parents[1] / "fixtures"
runner = CliRunner()


def test_infer_and_export_mermaid(tmp_path: Path) -> None:
    store_path = tmp_path / "ontolog.db"
    infer_result = runner.invoke(
        app,
        [
            "infer",
            str(FIXTURES / "controlboard.log"),
            "--store",
            str(store_path),
        ],
    )
    assert infer_result.exit_code == 0, infer_result.output

    export_result = runner.invoke(
        app,
        ["export", "mermaid", "--store", str(store_path)],
    )
    assert export_result.exit_code == 0, export_result.output
    assert "erDiagram" in export_result.stdout
    assert "Interface" in export_result.stdout or "Controlboard" in export_result.stdout
