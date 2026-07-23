"""Integration tests for provider pipeline on controlboard fixture."""

from __future__ import annotations

from pathlib import Path

from ontolog.config import default_config
from ontolog.evidence import load_evidence_graph
from ontolog.storage import SqliteTemplateStore
from ontolog.templates.extractor import ExtractOptions, extract_templates

FIXTURES = Path(__file__).resolve().parents[1] / "fixtures"


def test_controlboard_has_ipv4_and_hex_types(tmp_path: Path) -> None:
    store_path = tmp_path / "ontolog.db"
    extract_templates(
        FIXTURES / "controlboard.log",
        ExtractOptions(),
        store=SqliteTemplateStore(store_path),
    )
    graph = load_evidence_graph(store_path, config=default_config())
    type_labels = {node.label for node in graph.nodes() if node.kind.value == "type"}
    assert "ipv4" in type_labels
    assert "hex" in type_labels


def test_controlboard_has_controlboard_entity(tmp_path: Path) -> None:
    store_path = tmp_path / "ontolog.db"
    extract_templates(
        FIXTURES / "controlboard.log",
        ExtractOptions(),
        store=SqliteTemplateStore(store_path),
    )
    graph = load_evidence_graph(store_path, config=default_config())
    assert graph.get_node("entity:controlboard") is not None
