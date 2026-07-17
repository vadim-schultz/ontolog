"""Tests for ontolog graph CLI."""

from __future__ import annotations

from pathlib import Path

from typer.testing import CliRunner

from ontolog.cli.main import app
from ontolog.models.template import Template
from ontolog.storage import SqliteTemplateStore

FIXTURES = Path(__file__).resolve().parents[1] / "fixtures"
runner = CliRunner()


def test_graph_show_exits_zero(tmp_path: Path) -> None:
    store_path = tmp_path / "ontolog.db"
    result = runner.invoke(app, ["graph", "--show", "--store", str(store_path)])

    assert result.exit_code == 0, result.output


def test_graph_show_prints_counts(tmp_path: Path) -> None:
    store_path = tmp_path / "ontolog.db"
    result = runner.invoke(app, ["graph", "--show", "--store", str(store_path)])

    assert result.exit_code == 0
    assert "nodes:" in result.stderr
    assert "edges:" in result.stderr


def test_graph_show_empty_counts(tmp_path: Path) -> None:
    store_path = tmp_path / "ontolog.db"
    result = runner.invoke(app, ["graph", "--show", "--store", str(store_path)])

    assert result.exit_code == 0
    assert "nodes: 0" in result.stderr
    assert "edges: 0" in result.stderr


def test_graph_show_opens_store(tmp_path: Path) -> None:
    store_path = tmp_path / "ontolog.db"
    store = SqliteTemplateStore(store_path)
    try:
        store.upsert_template(
            Template(id="cluster_1", template="PacketSent destination=<IP>"),
        )
    finally:
        store.close()

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

    graph_result = runner.invoke(app, ["graph", "--show", "--store", str(store_path)])
    assert graph_result.exit_code == 0


def test_graph_show_nonzero_after_templates(tmp_path: Path) -> None:
    store_path = tmp_path / "ontolog.db"
    templates_result = runner.invoke(
        app,
        [
            "templates",
            str(FIXTURES / "controlboard.log"),
            "--store",
            str(store_path),
        ],
    )
    assert templates_result.exit_code == 0

    graph_result = runner.invoke(app, ["graph", "--show", "--store", str(store_path)])
    assert graph_result.exit_code == 0
    assert "nodes: 0" not in graph_result.stderr
    assert "entities:" in graph_result.stderr


def test_graph_show_includes_candidate_counts(tmp_path: Path) -> None:
    store_path = tmp_path / "ontolog.db"
    templates_result = runner.invoke(
        app,
        [
            "templates",
            str(FIXTURES / "controlboard.log"),
            "--store",
            str(store_path),
        ],
    )
    assert templates_result.exit_code == 0

    graph_result = runner.invoke(app, ["graph", "--show", "--store", str(store_path)])
    assert graph_result.exit_code == 0
    assert "entities:" in graph_result.stderr
    assert "entities: 0" not in graph_result.stderr
