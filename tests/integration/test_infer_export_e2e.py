"""End-to-end integration tests for infer and export."""

from __future__ import annotations

import json
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


def test_infer_exports_domain_json() -> None:
    result = runner.invoke(
        app,
        ["infer", str(FIXTURES / "controlboard.log"), "--format", "domain-json"],
    )
    assert result.exit_code == 0, result.output
    payload = json.loads(result.stdout)
    assert "entities" in payload


def test_infer_exports_evidence_graph() -> None:
    result = runner.invoke(
        app,
        ["infer", str(FIXTURES / "controlboard.log"), "--format", "evidence-graph"],
    )
    assert result.exit_code == 0, result.output
    payload = json.loads(result.stdout)
    assert "nodes" in payload
    assert "edges" in payload


def test_infer_exports_full_bundle() -> None:
    result = runner.invoke(
        app,
        ["infer", str(FIXTURES / "controlboard.log"), "--format", "full"],
    )
    assert result.exit_code == 0, result.output
    payload = json.loads(result.stdout)
    assert "domain_model" in payload
    assert "evidence_graph" in payload
    assert "templates" in payload
